"""
sv_payload_builder — Traduce un Sales Invoice de ERPNext al contrato del gateway v2.

SIN secretos en el payload: password_pri, api_password y tokens no se incluyen.
El gateway los resuelve internamente desde sus variables de entorno.

Uso:
    payload = build_emit_request(doc, tipo_dte)
    # Luego: requests.post(url, json=payload)
"""

import frappe
from frappe.utils import now_datetime


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def build_emit_request(doc, tipo_dte: str) -> dict:
    """
    Construye el dict para POST /v2/dte/emit a partir del Sales Invoice y settings.

    Args:
        doc:      Sales Invoice document (frappe.get_doc).
        tipo_dte: "01"=FE, "03"=CCF, "05"=NC.

    Returns:
        dict sin secretos listo para serializar a JSON.
    """
    settings = frappe.get_single("SV DTE Settings")
    estab = _get_establishment(settings)

    payload = {
        "tipo_dte":            tipo_dte,
        "ambiente":            settings.get("ambiente") or "00",
        "docname":             doc.name,
        "company":             doc.company,
        "posting_date":        str(doc.posting_date),
        "posting_time":        str(doc.posting_time or "00:00:00"),
        "currency":            "USD",
        "receptor":            _build_receptor(doc, tipo_dte),
        "items":               _build_items(doc),
        "grand_total":         float(doc.grand_total or 0),
        "total_iva":           _calc_total_iva(doc),
        "condicion_operacion": 1,
        "pagos":               [],
        "emisor":              _build_emisor_settings(settings, estab),
        "idempotency_key":     (
            f"{frappe.local.site}:Sales Invoice:{doc.name}:{tipo_dte}:"
            f"{settings.get('ambiente') or '00'}"
        ),
    }

    if tipo_dte == "05":
        payload.update(_build_nc_extras(doc))

    return payload


# ---------------------------------------------------------------------------
# Builders internos
# ---------------------------------------------------------------------------

def _get_establishment(settings) -> object:
    """Retorna el establecimiento default de los settings."""
    estab_name = settings.get("establecimiento_default")
    if not estab_name:
        frappe.throw(
            "SV DTE Settings no tiene establecimiento default configurado. "
            "Seleccione uno en el campo 'Establecimiento Default'."
        )
    return frappe.get_doc("SV DTE Establishment", estab_name)


def _build_emisor_settings(settings, estab) -> dict:
    """
    Construye el dict del emisor SIN secretos.
    url_firmador sí se incluye (no es un secreto).
    """
    return {
        "nit":                 settings.get("nit_emisor") or "",
        "nrc":                 (settings.get("nrc_emisor") or "").replace("-", ""),
        "nombre":              settings.get("nombre_emisor") or "",
        "nombre_comercial":    settings.get("nombre_comercial") or None,
        "cod_actividad":       settings.get("cod_actividad") or "",
        "desc_actividad":      settings.get("desc_actividad") or "",
        "tipo_establecimiento": estab.get("tipo_establecimiento") or "02",
        "cod_estable_mh":      estab.get("cod_estable_mh") or "M001",
        "cod_estable":         estab.get("cod_estable") or None,
        "cod_punto_venta_mh":  estab.get("cod_punto_venta_mh") or "P001",
        "cod_punto_venta":     estab.get("cod_punto_venta") or None,
        "departamento":        estab.get("departamento") or "05",
        "municipio":           estab.get("municipio") or "25",
        "complemento":         estab.get("complemento") or "",
        "telefono":            estab.get("telefono") or settings.get("telefono") or "22222222",
        "correo":              settings.get("correo") or "correo@empresa.com",
        "url_firmador":        settings.get("url_firmador") or "http://host.docker.internal:8113/firmardocumento/",
        "nit_firmador":        settings.get("nit_firmador") or None,
        # SIN: password_pri, api_password
    }


def _build_receptor(doc, tipo_dte: str) -> dict:
    """
    Construye el dict del receptor.
    CCF requiere NIT y NRC desde el Customer (sv_nit, sv_nrc).
    FE: solo nombre + datos opcionales.
    """
    receptor: dict = {
        "nombre":    doc.get("customer_name") or doc.get("customer") or "Consumidor Final",
        "correo":    doc.get("contact_email") or None,
        "telefono":  doc.get("contact_mobile") or None,
    }

    if tipo_dte in ("03", "05") and doc.get("customer"):
        try:
            customer = frappe.get_doc("Customer", doc.customer)
            receptor["nit"] = customer.get("sv_nit") or None
            receptor["nrc"] = customer.get("sv_nrc") or None
            receptor["cod_actividad"] = customer.get("sv_cod_actividad") or None
            receptor["tipo_doc_identificacion"] = "02"  # NIT
            receptor["num_documento"] = customer.get("sv_nit") or None
        except frappe.DoesNotExistError:
            pass

    return receptor


def _build_items(doc) -> list[dict]:
    """
    Convierte las líneas de Sales Invoice a DTEItemRequest dicts.
    venta_gravada = net_amount (pre-IVA — ERPNext ya aplicó descuentos).
    precio_unitario = net_rate (pre-IVA).
    """
    items = []
    for i, line in enumerate(doc.get("items") or [], start=1):
        items.append({
            "num_item":        i,
            "tipo_item":       2,   # 2=Servicios por defecto (ajustar en Sprint 3 desde Item)
            "descripcion":     line.get("item_name") or line.get("item_code") or "",
            "cantidad":        float(line.get("qty") or 1),
            "unidad_medida":   59,  # 59=Unidad
            "precio_unitario": float(line.get("net_rate") or 0),
            "descuento":       0.0,
            "venta_no_sujeta": 0.0,
            "venta_exenta":    0.0,
            "venta_gravada":   float(line.get("net_amount") or 0),
            "tributos":        ["20"],
            "codigo_interno":  line.get("item_code") or None,
        })
    return items


def _calc_total_iva(doc) -> float:
    """Suma el IVA incluido en los items (total_taxes_and_charges si aplica)."""
    return float(doc.get("total_taxes_and_charges") or 0)


def _build_nc_extras(doc) -> dict:
    """Campos adicionales para NC (tipo 05)."""
    return {
        "documento_relacionado_codigo": doc.get("sv_dte_generation_code") or doc.get("return_against"),
        "documento_relacionado_tipo":   doc.get("sv_dte_document_type") or "01",
        "documento_relacionado_fecha":  str(doc.get("posting_date") or ""),
    }
