"""
API DTE — integración con el DTE Gateway (FastAPI :8100) v2.

Endpoints whitelisted llamables desde Frappe via:
  /api/method/erpnext_localization_sv.api.dte.<función>

Sprint 2: flujo real — payload builder + /v2/dte/emit + logs sanitizados.
Los secretos (password_pri, api_password) nunca aparecen en el payload,
en sv_dte_last_payload ni en SV DTE Log.
"""

import os
from datetime import datetime

import frappe
import requests
from frappe.utils import now_datetime

from erpnext_localization_sv.config.sv_fiscal_constants import DTE_GATEWAY_URL as _DTE_GATEWAY_URL_DEFAULT
from erpnext_localization_sv.api.sv_payload_builder import build_emit_request

# Timeout ajustado para flujo real: firma (~3s) + MH (~8s × reintentos)
_GATEWAY_TIMEOUT = 30

# Claves sensibles que NO deben aparecer en logs ni en campos de la Sales Invoice
_LOG_SENSITIVE_KEYS = frozenset({
    "password_pri", "api_password", "passwordPri",
    "firmaElectronica", "token", "body",
    "FIRMADOR_PASSWORD_PRI", "MH_API_PASSWORD",
})


# ---------------------------------------------------------------------------
# Resolución de la URL base del gateway
# ---------------------------------------------------------------------------

def _get_gateway_base_url() -> str:
    site_config_url: str | None = frappe.conf.get("dte_gateway_url")
    if site_config_url:
        return site_config_url.rstrip("/")

    env_url: str | None = os.environ.get("DTE_GATEWAY_URL")
    if env_url:
        return env_url.rstrip("/")

    return _DTE_GATEWAY_URL_DEFAULT.rstrip("/")


def _gateway_url(path: str) -> str:
    return f"{_get_gateway_base_url()}/{path.lstrip('/')}"


# ---------------------------------------------------------------------------
# Sanitización de logs
# ---------------------------------------------------------------------------

def _parse_mh_datetime(dt_str: str | None) -> str | None:
    """Convierte 'DD/MM/YYYY HH:MM:SS' (MH) → 'YYYY-MM-DD HH:MM:SS' (MySQL)."""
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return dt_str


def _sanitize_for_log(data) -> object:
    """Elimina campos sensibles recursivamente antes de persistir."""
    if isinstance(data, dict):
        return {
            k: "***REDACTED***" if k in _LOG_SENSITIVE_KEYS else _sanitize_for_log(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_sanitize_for_log(item) for item in data]
    return data


# ---------------------------------------------------------------------------
# SV DTE Log
# ---------------------------------------------------------------------------

def _write_dte_log(
    docname: str,
    tipo_dte: str,
    payload: dict,
    result: dict,
    tipo_evento: str = "emision",
    codigo_generacion: str | None = None,
) -> None:
    try:
        log = frappe.new_doc("SV DTE Log")
        log.reference_doctype = "Sales Invoice"
        log.reference_docname = docname
        log.sales_invoice     = docname
        log.tipo_evento       = tipo_evento
        log.ambiente          = payload.get("ambiente", "00")
        log.codigo_generacion = (
            codigo_generacion
            or result.get("generation_code")
            or result.get("uuid_dte")
            or result.get("event_uuid")
        )
        log.http_status       = 200
        log.estado_resultante = result.get("estado") or result.get("status")
        log.request_json      = frappe.as_json(_sanitize_for_log(payload), indent=2)
        log.response_json     = frappe.as_json(_sanitize_for_log(result), indent=2)
        log.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as exc:
        frappe.logger().warning("[erpnext_localization_sv] SV DTE Log falló: %s", exc)


# ---------------------------------------------------------------------------
# Endpoints whitelisted
# ---------------------------------------------------------------------------

@frappe.whitelist()
def ping_gateway() -> dict:
    """Verifica que el DTE Gateway esté en línea."""
    url = _gateway_url("/health")
    try:
        response = requests.get(url, timeout=_GATEWAY_TIMEOUT)
        response.raise_for_status()
        return {"gateway_url": url, "gateway_response": response.json()}
    except requests.exceptions.ConnectionError:
        frappe.throw(f"No se pudo conectar al DTE Gateway en {url}")
    except requests.exceptions.Timeout:
        frappe.throw(f"Timeout al conectar con el DTE Gateway ({_GATEWAY_TIMEOUT}s)")
    except requests.exceptions.HTTPError as exc:
        frappe.throw(f"DTE Gateway respondió con error: {exc}")


@frappe.whitelist()
def emit_dte(doctype: str, docname: str) -> dict:
    """
    Emite un DTE para el Sales Invoice indicado.

    Llama a /v2/dte/emit con el payload completo (sin secretos).
    Persiste el resultado en los campos DTE de la Sales Invoice y crea SV DTE Log.

    Args:
        doctype: Debe ser "Sales Invoice".
        docname: Nombre del documento (ej. "SINV-0001").

    Returns:
        Respuesta JSON del gateway (sanitizada — sin firma ni tokens).
    """
    if not doctype or not docname:
        frappe.throw("doctype y docname son requeridos")

    if doctype != "Sales Invoice":
        frappe.throw(f"emit_dte solo soporta 'Sales Invoice'. Recibido: {doctype}")

    try:
        doc = frappe.get_doc(doctype, docname)
    except frappe.DoesNotExistError:
        frappe.throw(f"Documento no encontrado: {doctype} / {docname}")

    if doc.get("sv_estado_mh") == "PROCESADO":
        frappe.throw(
            "Este DTE ya fue PROCESADO por MH. Use 'Invalidar DTE' si desea invalidarlo.",
            title="DTE ya procesado"
        )

    # Determinar tipo DTE desde el campo del documento o default FE.
    # sv_dte_document_type almacena etiquetas ("FE","CCF","NC","ND") o códigos legacy ("01","03","05","06").
    _label_map = {"FE": "01", "CCF": "03", "NC": "05", "ND": "06"}
    raw_tipo = doc.get("sv_dte_document_type") or "FE"
    tipo_dte = _label_map.get(raw_tipo, raw_tipo) or "01"

    # Construir payload completo sin secretos
    payload = build_emit_request(doc, tipo_dte)

    # POST al gateway v2
    url = _gateway_url("/v2/dte/emit")
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
    gen_code = result.get("generation_code") or result.get("uuid_dte")

    # Computar URL del portal de consulta pública MH (Sprint 6, corregido Sprint 7).
    # El portal admin.factura.gob.sv/consultaPublica es una SPA Angular que NO acepta
    # parámetros en la URL para pre-poblar el formulario — solo usa la URL base.
    # El usuario ingresa el codigoGeneracion manualmente en el portal.
    # Solo si url_verificacion_mh está configurada en SV DTE Settings. No lanzar excepción si falta.
    _qr_url = ""
    try:
        _settings = frappe.get_single("SV DTE Settings")
        _base_url = (_settings.get("url_verificacion_mh") or "").strip().rstrip("/")
        if gen_code and _base_url:
            _qr_url = _base_url  # URL del portal — no se añaden query params (SPA no los lee)
    except Exception:
        pass  # URL de QR es opcional — no bloquear la emisión

    # Persistir en Sales Invoice (solo datos limpios — sin firma)
    frappe.db.set_value("Sales Invoice", docname, {
        "sv_dte_status":           result.get("status"),
        "sv_dte_generation_code":  gen_code,
        "sv_dte_control_number":   result.get("control_number"),
        "sv_dte_sent_at":          now_datetime(),
        "sv_dte_last_payload":     frappe.as_json(_sanitize_for_log(payload), indent=2),
        "sv_dte_last_response":    frappe.as_json(_sanitize_for_log(result), indent=2),
        "sv_estado_mh":            result.get("estado"),
        "sv_clasifica_msg":        result.get("clasifica_msg"),
        "sv_codigo_msg":           result.get("codigo_msg"),
        "sv_sello_recepcion":      result.get("sello_recibido"),
        "sv_fecha_procesamiento":  _parse_mh_datetime(result.get("fh_procesamiento")),
        "sv_observaciones_mh":     frappe.as_json(result.get("observaciones") or [], indent=2),
        # Sprint 4: persistir IVA calculado en el DTE como fuente principal para anulación
        "sv_total_iva":            float(payload.get("total_iva") or 0),
        # Sprint 6: URL de verificación MH (vacía si url_verificacion_mh no está configurada)
        "sv_dte_qr_url":           _qr_url,
    })
    frappe.db.commit()

    # Sincronizar SV DTE Document (índice operativo)
    try:
        from erpnext_localization_sv.api.dte_document_sync import sync_on_emit
        sync_on_emit(
            source_doctype="Sales Invoice",
            source_docname=docname,
            generation_code=gen_code,
            control_number=result.get("control_number"),
            mh_status=result.get("estado"),
            dte_type_label=raw_tipo,
            dte_type_code=tipo_dte,
            reception_seal=result.get("sello_recibido"),
            mh_processed_at=_parse_mh_datetime(result.get("fh_procesamiento")),
            ambiente=(_settings.get("ambiente") if "_settings" in dir() else None) or "00",
            company=doc.company,
            customer=doc.customer,
            customer_name=doc.customer_name,
            mh_verification_url=_qr_url,
        )
    except Exception as _sync_exc:
        frappe.logger().warning(
            "[erpnext_localization_sv] sync_on_emit falló para %s: %s", docname, _sync_exc
        )

    # Crear SV DTE Log (sanitizado)
    _write_dte_log(docname, tipo_dte, payload, result, tipo_evento="emision", codigo_generacion=gen_code)

    # Mensajes accionables desde MH
    obs = result.get("observaciones") or []
    estado_emision = result.get("estado") or ""
    _ESTADOS_EXITOSOS = {"PROCESADO"}
    if estado_emision and estado_emision not in _ESTADOS_EXITOSOS:
        obs_text = "\n".join(f"• {o}" for o in obs) if obs else f"Estado MH: {estado_emision}"
        frappe.throw(obs_text, title=f"DTE {estado_emision} por MH")
    elif obs:
        frappe.msgprint(
            "\n".join(f"• {o}" for o in obs),
            title="Observaciones MH",
            indicator="orange",
        )

    frappe.logger().info(
        "[erpnext_localization_sv] emit_dte docname=%s gen_code=%s estado=%s",
        docname, gen_code, result.get("estado") or result.get("status"),
    )

    # Retornar resultado sanitizado (sin firma)
    return _sanitize_for_log(result)


@frappe.whitelist()
def get_dte_status(docname: str) -> dict:
    """
    Consulta el estado de un DTE en el MH por código de generación.

    El gateway resuelve el token internamente (api_password via env var).
    No se envía api_password en el request.

    Args:
        docname: Nombre del Sales Invoice con DTE emitido.
    """
    if not docname:
        frappe.throw("docname es requerido")

    doc = frappe.get_doc("Sales Invoice", docname)
    gen_code = doc.get("sv_dte_generation_code")
    if not gen_code:
        frappe.throw("El documento no tiene Código de Generación DTE. Emita el DTE primero.")

    settings = frappe.get_single("SV DTE Settings")
    # Mapear label → código para el campo tipo_dte (MH requiere "01", "03", "05")
    _label_map = {"FE": "01", "CCF": "03", "NC": "05"}
    raw_tipo = doc.get("sv_dte_document_type") or "FE"
    tipo_dte_code = _label_map.get(raw_tipo, raw_tipo) or "01"

    payload = {
        "tipo_dte":          tipo_dte_code,
        "codigo_generacion": gen_code,
        "ambiente":          settings.get("ambiente") or "00",
        "nit_emisor":        settings.get("nit_emisor") or "",
        # api_password NO se incluye — el gateway lo resuelve via secret_resolver
    }

    url = _gateway_url("/v2/dte/status")
    try:
        response = requests.post(url, json=payload, timeout=_GATEWAY_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        frappe.throw(f"No se pudo conectar al DTE Gateway en {url}")
    except requests.exceptions.Timeout:
        frappe.throw(f"Timeout ({_GATEWAY_TIMEOUT}s) consultando estado DTE")
    except requests.exceptions.HTTPError as exc:
        frappe.throw(f"DTE Gateway respondió con error: {exc}")

    result = response.json()

    # Persistir el estado actual de MH en el Sales Invoice
    estado_mh = result.get("estado")
    if estado_mh:
        frappe.db.set_value("Sales Invoice", docname, {"sv_estado_mh": estado_mh})
        frappe.db.commit()

    # Sincronizar SV DTE Document
    if estado_mh and gen_code:
        try:
            from erpnext_localization_sv.api.dte_document_sync import sync_on_status_check
            sync_on_status_check(generation_code=gen_code, mh_status=estado_mh)
            frappe.db.commit()
        except Exception:
            pass

    return result
