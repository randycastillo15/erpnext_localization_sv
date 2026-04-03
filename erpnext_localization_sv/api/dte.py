"""
API DTE — stubs de integración con el DTE Gateway (FastAPI :8100).

Estos endpoints son llamables desde Frappe via:
  /api/method/erpnext_localization_sv.api.dte.<función>

La implementación real (firma XML, envío al MH, manejo de respuesta)
se añadirá cuando el DocType de configuración y el gateway estén listos.
"""

import os

import frappe
import requests
from frappe.utils import now_datetime

from erpnext_localization_sv.config.sv_fiscal_constants import DTE_GATEWAY_URL as _DTE_GATEWAY_URL_DEFAULT

# Timeout por defecto para llamadas al gateway (segundos)
_GATEWAY_TIMEOUT = 5


# ---------------------------------------------------------------------------
# Resolución de la URL base del gateway
# Prioridad: site_config.json > variable de entorno > constante (default)
# ---------------------------------------------------------------------------


def _get_gateway_base_url() -> str:
	"""
	Devuelve la URL base del DTE Gateway según el siguiente orden de precedencia:

	1. ``dte_gateway_url`` en site_config.json   (frappe.conf)
	2. Variable de entorno ``DTE_GATEWAY_URL``
	3. Constante ``DTE_GATEWAY_URL`` en sv_fiscal_constants.py
	       → default: http://host.docker.internal:8100
	"""
	# 1. site_config.json (por site, permite override sin reiniciar)
	site_config_url: str | None = frappe.conf.get("dte_gateway_url")
	if site_config_url:
		return site_config_url.rstrip("/")

	# 2. Variable de entorno (útil en CI o entornos sin acceso a site_config)
	env_url: str | None = os.environ.get("DTE_GATEWAY_URL")
	if env_url:
		return env_url.rstrip("/")

	# 3. Default hardcodeado en constantes
	return _DTE_GATEWAY_URL_DEFAULT.rstrip("/")


def _gateway_url(path: str) -> str:
	"""Construye la URL completa del gateway evitando doble slash."""
	return f"{_get_gateway_base_url()}/{path.lstrip('/')}"


# ---------------------------------------------------------------------------
# Endpoints whitelisted
# ---------------------------------------------------------------------------


@frappe.whitelist()
def ping_gateway() -> dict:
	"""
	Verifica que el DTE Gateway esté en línea.
	Llama GET <gateway_base_url>/health y devuelve su respuesta.
	La URL se resuelve en tiempo de ejecución (site_config > env > default).
	"""
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
	Emite un DTE para el documento indicado enviando el payload al gateway.

	Solo soporta Sales Invoice en esta fase.
	No firma XML ni conecta al Ministerio de Hacienda todavía.

	Args:
		doctype: DocType del documento origen — debe ser "Sales Invoice".
		docname: Nombre del documento (ej. "SINV-0001").

	Returns:
		Respuesta JSON del gateway: {status, uuid_dte, received_at, mode, echo}.
	"""
	if not doctype or not docname:
		frappe.throw("doctype y docname son requeridos")

	# 1. Solo Sales Invoice soportado por ahora
	if doctype != "Sales Invoice":
		frappe.throw(
			f"emit_dte solo soporta 'Sales Invoice' por ahora. Recibido: {doctype}"
		)

	# 2. Leer documento desde ERPNext
	try:
		doc = frappe.get_doc(doctype, docname)
	except frappe.DoesNotExistError:
		frappe.throw(f"Documento no encontrado: {doctype} / {docname}")

	# 3. Construir payload mínimo de Sales Invoice
	payload = {
		"doctype": doc.doctype,
		"docname": doc.name,
		"company": doc.get("company"),
		"posting_date": str(doc.get("posting_date") or ""),
		"currency": doc.get("currency"),
		"grand_total": float(doc.get("grand_total") or 0),
		"customer": doc.get("customer"),
	}

	# 4. POST al gateway
	url = _gateway_url("/dte/emit")
	try:
		response = requests.post(url, json=payload, timeout=_GATEWAY_TIMEOUT)
		response.raise_for_status()
	except requests.exceptions.ConnectionError:
		frappe.throw(f"No se pudo conectar al DTE Gateway en {url}")
	except requests.exceptions.Timeout:
		frappe.throw(f"Timeout al conectar con el DTE Gateway ({_GATEWAY_TIMEOUT}s)")
	except requests.exceptions.HTTPError as exc:
		frappe.throw(f"DTE Gateway respondió con error: {exc}")

	# 5. Persistir resultado en la Sales Invoice
	result = response.json()
	gen_code = result.get("generation_code") or result.get("uuid_dte")
	frappe.db.set_value("Sales Invoice", docname, {
		"sv_dte_status":           result.get("status"),
		"sv_dte_uuid":             result.get("uuid_dte"),
		"sv_dte_generation_code":  gen_code,
		"sv_dte_control_number":   result.get("control_number"),
		"sv_dte_sent_at":          now_datetime(),
		"sv_dte_last_payload":     frappe.as_json(payload, indent=2),
		"sv_dte_last_response":    frappe.as_json(result, indent=2),
		"sv_estado_mh":            result.get("estado"),
		"sv_clasifica_msg":        result.get("clasificaMsg"),
		"sv_codigo_msg":           result.get("codigoMsg"),
		"sv_sello_recepcion":      result.get("selloRecibido"),
		"sv_fecha_procesamiento":  result.get("fhProcesamiento"),
		"sv_observaciones_mh":     frappe.as_json(result.get("observaciones") or [], indent=2),
	})
	frappe.db.commit()

	# 6. Retornar respuesta del gateway
	frappe.logger().info(
		"[erpnext_localization_sv] emit_dte — docname=%s generation_code=%s mode=%s estado=%s",
		docname,
		gen_code,
		result.get("mode"),
		result.get("estado") or result.get("status"),
	)
	return result


@frappe.whitelist()
def get_dte_status(dte_uuid: str) -> dict:
	"""
	Stub: consulta el estado de un DTE previamente emitido.

	Args:
		dte_uuid: UUID del DTE asignado por el MH.

	Returns:
		dict con estado del DTE.

	TODO: implementar cuando exista endpoint GET /dte/{uuid}/status en el gateway.
	"""
	if not dte_uuid:
		frappe.throw("dte_uuid es requerido")

	frappe.logger().info(
		"[erpnext_localization_sv] get_dte_status llamado — uuid=%s (stub)",
		dte_uuid,
	)

	return {
		"status": "stub",
		"dte_uuid": dte_uuid,
		"mh_status": None,
		"message": "get_dte_status no implementado aún — pendiente integración con gateway",
	}
