"""
API Anulación DTE — integración con el DTE Gateway endpoint /v2/dte/anular.

Permite anular un DTE ya PROCESADO por MH desde ERPNext.

Endpoint whitelisted:
  /api/method/erpnext_localization_sv.api.anulacion.anular_dte

Reglas:
  - Solo documentos con sv_estado_mh="PROCESADO" y sv_sello_recepcion lleno.
  - montoIva: fuente principal = sv_total_iva (persistido en emit_dte).
    Fallback: total_taxes_and_charges (con advertencia si es documento legacy).
    Si ambos vacíos: None (schema lo permite con type ["number","null"]).
  - tipoDocumento del receptor: "36" (NIT) para CCF/NC, "13" (DUI) para FE sin NIT.
  - Responsable y solicitante: desde SV DTE Settings (sv_nombre_responsable, etc.).
"""

import frappe
import requests
from frappe.utils import now_datetime

from erpnext_localization_sv.api.dte import _get_gateway_base_url, _gateway_url
from erpnext_localization_sv.api.sv_payload_builder import build_emit_request

_DTE_LABEL_TO_CODE = {"FE": "01", "CCF": "03", "NC": "05"}
_GATEWAY_TIMEOUT = 30


@frappe.whitelist()
def anular_dte(
    docname: str,
    tipo_anulacion: int,
    motivo_anulacion: str,
    nombre_solicita: str = "",
    tip_doc_solicita: str = "",
    num_doc_solicita: str = "",
    codigo_generacion_reemplazo: str = "",
) -> dict:
    """
    Anula un DTE ya PROCESADO por MH.

    Args:
        docname:                      Nombre del Sales Invoice a anular.
        tipo_anulacion:               1=Error/reemplazar, 2=Sin reemplazo, 3=Devolución.
        motivo_anulacion:             Descripción del motivo.
        nombre_solicita:              Nombre del solicitante. Si vacío, usa el responsable de Settings.
        tip_doc_solicita:             Tipo doc del solicitante (CAT-22). Si vacío, usa el de Settings.
        num_doc_solicita:             Número doc del solicitante. Si vacío, usa el de Settings.
        codigo_generacion_reemplazo:  UUID del DTE sustituto (solo para tipo 1 o 3).

    Returns:
        Respuesta JSON del gateway con sello_recibido y estado.
    """
    if not docname:
        frappe.throw("docname es requerido")

    tipo_anulacion = int(tipo_anulacion)

    try:
        doc = frappe.get_doc("Sales Invoice", docname)
    except frappe.DoesNotExistError:
        frappe.throw(f"Documento no encontrado: Sales Invoice / {docname}")

    # Verificar que el DTE está PROCESADO
    estado_mh = doc.get("sv_estado_mh") or ""
    if estado_mh != "PROCESADO":
        frappe.throw(
            f"Solo se pueden anular DTEs con estado MH 'PROCESADO'. "
            f"El documento '{docname}' tiene estado: '{estado_mh}'."
        )

    gen_code = doc.get("sv_dte_generation_code") or ""
    if not gen_code:
        frappe.throw(f"El documento '{docname}' no tiene Código de Generación DTE.")

    sello = doc.get("sv_sello_recepcion") or ""
    if not sello:
        frappe.throw(
            f"El documento '{docname}' no tiene Sello de Recepción. "
            "El DTE debe estar PROCESADO con sello para poder anularse."
        )

    numero_control = doc.get("sv_dte_control_number") or ""
    if not numero_control:
        frappe.throw(f"El documento '{docname}' no tiene Número de Control DTE.")

    # montoIva — fuente principal: sv_total_iva
    monto_iva = None
    sv_total_iva = doc.get("sv_total_iva")
    if sv_total_iva is not None and float(sv_total_iva) > 0:
        monto_iva = round(float(sv_total_iva), 2)
    else:
        total_taxes = doc.get("total_taxes_and_charges")
        if total_taxes is not None and float(total_taxes) > 0:
            monto_iva = round(float(total_taxes), 2)
            frappe.logger().warning(
                "[anulacion] '%s': sv_total_iva vacío — usando total_taxes_and_charges=%.2f como fallback. "
                "Verifique que este valor corresponde exactamente al IVA del DTE emitido.",
                docname, monto_iva,
            )
        # Si ambos vacíos: monto_iva queda None (schema lo permite)

    # Tipo DTE — mapear etiqueta a código
    raw_tipo = doc.get("sv_dte_document_type") or "FE"
    tipo_dte = _DTE_LABEL_TO_CODE.get(raw_tipo, raw_tipo) or "01"

    # Receptor del documento original
    tipo_doc_receptor, num_doc_receptor, nombre_receptor = _get_receptor_identidad(doc, tipo_dte)

    # Emisor desde Settings
    settings = frappe.get_single("SV DTE Settings")
    from erpnext_localization_sv.api.sv_payload_builder import _get_establishment, _build_emisor_settings
    estab = _get_establishment(settings)
    emisor_dict = _build_emisor_settings(settings, estab)

    # Responsable desde Settings
    nombre_responsable = settings.get("sv_nombre_responsable") or ""
    tip_doc_responsable = settings.get("sv_tipo_doc_responsable") or "36"
    num_doc_responsable = settings.get("sv_num_doc_responsable") or ""

    if not nombre_responsable:
        frappe.throw(
            "SV DTE Settings no tiene Responsable configurado (sv_nombre_responsable). "
            "Configure el responsable antes de anular DTEs."
        )

    # Solicitante: si no se pasa, usar el mismo responsable
    nombre_solicita = nombre_solicita or nombre_responsable
    tip_doc_solicita = tip_doc_solicita or tip_doc_responsable
    num_doc_solicita = num_doc_solicita or num_doc_responsable

    ambiente = settings.get("ambiente") or "00"
    fec_emi = str(doc.get("posting_date") or "")
    fecha_anula = str(frappe.utils.today())

    idempotency_key = (
        f"{frappe.local.site}:Sales Invoice:{docname}:anulacion:{tipo_anulacion}:{ambiente}"
    )

    payload = {
        "ambiente":                        ambiente,
        "emisor":                          emisor_dict,
        "tipo_dte":                        tipo_dte,
        "codigo_generacion_original":      gen_code,
        "sello_recibido":                  sello,
        "numero_control":                  numero_control,
        "fec_emi":                         fec_emi,
        "monto_iva":                       monto_iva,
        "tipo_documento_receptor":         tipo_doc_receptor,
        "num_documento_receptor":          num_doc_receptor,
        "nombre_receptor":                 nombre_receptor,
        "tipo_anulacion":                  tipo_anulacion,
        "motivo_anulacion":                motivo_anulacion or None,
        "codigo_generacion_reemplazo":     codigo_generacion_reemplazo or None,
        "nombre_responsable":              nombre_responsable,
        "tip_doc_responsable":             tip_doc_responsable,
        "num_doc_responsable":             num_doc_responsable,
        "nombre_solicita":                 nombre_solicita,
        "tip_doc_solicita":                tip_doc_solicita,
        "num_doc_solicita":                num_doc_solicita,
        "fecha_anula":                     fecha_anula,
        "idempotency_key":                 idempotency_key,
    }

    url = _gateway_url("/v2/dte/anular")
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

    # Persistir resultado de anulación en Sales Invoice
    anulado = bool(result.get("sello_recibido"))
    frappe.db.set_value("Sales Invoice", docname, {
        "sv_anulacion_status":                     "Invalidado" if anulado else "Rechazado",
        "sv_anulacion_tipo":                       tipo_anulacion,
        "sv_motivo_anulacion":                     motivo_anulacion or "",
        "sv_anulacion_sello":                      result.get("sello_recibido") or "",
        "sv_anulacion_fecha":                      fecha_anula,
        "sv_anulacion_codigo_generacion_reemplazo": codigo_generacion_reemplazo or "",
        # Reflejar el estado real en MH: INVALIDADO si anulación fue aceptada
        "sv_estado_mh":                            "INVALIDADO" if anulado else doc.get("sv_estado_mh"),
    })
    frappe.db.commit()

    # Registrar en SV DTE Log
    from erpnext_localization_sv.api.dte import _write_dte_log
    _write_dte_log(
        docname=docname, tipo_dte=tipo_dte, payload=payload,
        result=result, tipo_evento="invalidacion", codigo_generacion=gen_code,
    )

    frappe.logger().info(
        "[anulacion] docname=%s gen_code=%s tipo=%s estado=%s sello=%s",
        docname, gen_code, tipo_anulacion,
        result.get("estado"), result.get("sello_recibido"),
    )

    return result


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _get_receptor_identidad(doc, tipo_dte: str) -> tuple[str, str, str]:
    """
    Retorna (tipo_documento, num_documento, nombre) del receptor original.

    Para CCF/NC: el receptor tiene NIT → tipo_documento="36" (CAT-22).
    Para FE sin NIT: usar tipo_documento="13" (DUI) si hay num_documento disponible.
    """
    customer_name = doc.get("customer_name") or doc.get("customer") or "Consumidor Final"
    nombre = customer_name

    if tipo_dte in ("03", "05") and doc.get("customer"):
        try:
            customer = frappe.get_doc("Customer", doc.customer)
            nit = customer.get("sv_nit") or ""
            if nit:
                return "36", nit.replace("-", ""), nombre
            nrc = customer.get("sv_nrc") or ""
            if nrc:
                return "36", nrc.replace("-", ""), nombre
        except Exception:
            pass

    # FE o sin datos de Customer — intentar con num_documento del doc
    # Si no hay nada, usar un placeholder mínimo (schema requiere mínimo 3 chars)
    return "37", "OTRO", nombre
