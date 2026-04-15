"""
API Contingencia DTE — integración con el DTE Gateway endpoint /v2/contingencia/emit.

Permite reportar DTEs emitidos offline durante un período de contingencia.

Endpoint whitelisted:
  /api/method/erpnext_localization_sv.api.contingencia.emit_contingencia

Alcance Sprint 4:
  - Transmite el evento de contingencia tipo 14 al MH usando DTEs ya generados offline
    (cuyos sv_dte_generation_code ya están registrados en los Sales Invoices).
  - Persiste el sello y event_uuid en cada Sales Invoice incluido.
  - El ciclo completo (emisión automática offline + regularización) es trabajo futuro.
"""

import json

import frappe
import requests

from erpnext_localization_sv.api.dte import _gateway_url
from erpnext_localization_sv.api.sv_payload_builder import _get_establishment, _build_emisor_settings

_DTE_LABEL_TO_CODE = {"FE": "01", "CCF": "03", "NC": "05"}
_GATEWAY_TIMEOUT = 30


@frappe.whitelist()
def emit_contingencia(
    docnames_json: str,
    tipo_contingencia: int,
    motivo_contingencia: str = "",
    f_inicio: str = "",
    h_inicio: str = "",
    f_fin: str = "",
    h_fin: str = "",
) -> dict:
    """
    Transmite un evento de contingencia tipo 14 al MH.

    Args:
        docnames_json:      JSON list de nombres de Sales Invoice (ej. '["SINV-X","SINV-Y"]').
        tipo_contingencia:  1-5. Si es 5, motivo_contingencia es obligatorio.
        motivo_contingencia: Descripción libre del motivo. Requerido si tipo=5.
        f_inicio:           Fecha inicio contingencia (YYYY-MM-DD).
        h_inicio:           Hora inicio (HH:MM:SS).
        f_fin:              Fecha fin contingencia (YYYY-MM-DD).
        h_fin:              Hora fin (HH:MM:SS).

    Returns:
        Respuesta JSON del gateway con event_uuid, sello_recibido y estado.
    """
    tipo_contingencia = int(tipo_contingencia)

    try:
        docnames = json.loads(docnames_json)
    except (ValueError, TypeError):
        frappe.throw("docnames_json debe ser una lista JSON válida de nombres de Sales Invoice.")

    if not docnames:
        frappe.throw("docnames_json no puede estar vacío.")

    if len(docnames) > 1000:
        frappe.throw(f"Se pueden incluir máximo 1000 documentos por evento (recibidos: {len(docnames)}).")

    if tipo_contingencia == 5 and not motivo_contingencia:
        frappe.throw("tipoContingencia=5 (Otro) requiere motivo_contingencia con descripción.")

    # Construir detalle — leer sv_dte_generation_code de cada Sales Invoice
    detalle = []
    for i, docname in enumerate(docnames, start=1):
        try:
            doc = frappe.get_doc("Sales Invoice", docname)
        except frappe.DoesNotExistError:
            frappe.throw(f"Sales Invoice '{docname}' no encontrado.")

        gen_code = doc.get("sv_dte_generation_code") or ""
        if not gen_code:
            frappe.throw(
                f"Sales Invoice '{docname}' no tiene Código de Generación DTE. "
                "Solo se pueden incluir en contingencia documentos con codigoGeneracion asignado."
            )

        raw_tipo = doc.get("sv_dte_document_type") or "FE"
        tipo_doc = _DTE_LABEL_TO_CODE.get(raw_tipo, raw_tipo) or "01"

        detalle.append({
            "no_item":           i,
            "codigo_generacion": gen_code,
            "tipo_doc":          tipo_doc,
        })

    # Emisor desde Settings
    settings = frappe.get_single("SV DTE Settings")
    estab = _get_establishment(settings)
    emisor_dict = _build_emisor_settings(settings, estab)
    ambiente = settings.get("ambiente") or "00"

    # Responsable: datos del usuario logueado (requiere rol DTE Responsable)
    if "DTE Responsable" not in frappe.get_roles():
        frappe.throw(
            "No tienes el rol 'DTE Responsable'. "
            "Solicita acceso al administrador del sistema antes de reportar contingencias."
        )
    user_doc = frappe.get_doc("User", frappe.session.user)
    nombre_responsable = user_doc.full_name or ""
    tipo_doc_responsable = user_doc.get("sv_tipo_doc_responsable") or "36"
    num_doc_responsable = user_doc.get("sv_num_doc_responsable") or ""

    if not nombre_responsable or not num_doc_responsable:
        frappe.throw(
            "Tu perfil de usuario no tiene los datos de Responsable DTE completos "
            "(Tipo y Núm. Doc Responsable). "
            "Completa la sección 'Responsable DTE' en tu perfil antes de transmitir contingencias."
        )

    today = frappe.utils.today()
    import datetime
    now_time = datetime.datetime.now().strftime("%H:%M:%S")

    idempotency_key = (
        f"{frappe.local.site}:contingencia:{','.join(docnames[:5])}:{tipo_contingencia}:{ambiente}"
    )

    payload = {
        "ambiente":              ambiente,
        "emisor":                emisor_dict,
        "nombre_responsable":    nombre_responsable,
        "tipo_doc_responsable":  tipo_doc_responsable,
        "num_doc_responsable":   num_doc_responsable,
        "tipo_contingencia":     tipo_contingencia,
        "motivo_contingencia":   motivo_contingencia or None,
        "f_inicio":              f_inicio or today,
        "h_inicio":              h_inicio or "00:00:00",
        "f_fin":                 f_fin or today,
        "h_fin":                 h_fin or now_time,
        "detalle":               detalle,
        "idempotency_key":       idempotency_key,
    }

    url = _gateway_url("/v2/contingencia/emit")
    try:
        response = requests.post(url, json=payload, timeout=_GATEWAY_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        frappe.throw(f"No se pudo conectar al DTE Gateway en {url}")
    except requests.exceptions.Timeout:
        frappe.throw(f"Timeout al conectar con el DTE Gateway ({_GATEWAY_TIMEOUT}s)")
    except requests.exceptions.HTTPError as exc:
        error_detail = ""
        try:
            error_detail = exc.response.json().get("detail", "") if exc.response else ""
        except Exception:
            pass
        frappe.throw(f"DTE Gateway respondió con error: {exc} — {error_detail}")

    result = response.json()
    event_uuid = result.get("event_uuid") or ""
    sello = result.get("sello_recibido") or ""

    frappe.logger().info(
        "[contingencia] event_uuid=%s tipo=%s dtes=%d estado=%s sello=%s",
        event_uuid, tipo_contingencia, len(docnames),
        result.get("estado"), sello,
    )

    # Registrar en SV DTE Log (entrada representativa usando el primer docname)
    from erpnext_localization_sv.api.dte import _write_dte_log
    _write_dte_log(
        docname=docnames[0], tipo_dte="14", payload=payload,
        result=result, tipo_evento="contingencia", codigo_generacion=event_uuid,
    )

    return result
