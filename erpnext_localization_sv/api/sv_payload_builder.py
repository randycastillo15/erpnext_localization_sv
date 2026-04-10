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

# Mapeo de etiquetas del campo Select → código DTE para el gateway.
# El campo sv_dte_document_type almacena etiquetas legibles ("FE", "CCF", "NC")
# pero el gateway y el schema MH usan códigos numéricos ("01", "03", "05").
_DTE_LABEL_TO_CODE = {"FE": "01", "CCF": "03", "NC": "05", "ND": "06"}


def _resolve_municipio(value: str | None) -> str | None:
    """
    Convierte el valor del campo municipio al código numérico que espera el gateway.

    El campo sv_municipio / sv_direccion_municipio es un Link a SV Municipio cuyo
    name tiene formato "dept-codigo" (ej. "05-25"). El gateway solo necesita el
    código relativo (ej. "25").  Para datos legacy que ya almacenaban el código
    directamente, se retorna el valor sin cambios.
    """
    if not value:
        return None
    codigo = frappe.db.get_value("SV Municipio", value, "codigo")
    return codigo if codigo else value


def _get_receptor_address(doc, customer_name: str):
    """
    Resuelve el Address del receptor para un Sales Invoice.

    Cadena de resolución:
    1. doc.customer_address  — seleccionado explícitamente en el documento
    2. Dirección de facturación default del Customer
    3. None  — el llamador usará fallback legacy (campos sv_direccion_* del Customer)
    """
    # 1. Dirección explícita en el documento
    addr_name = doc.get("customer_address")
    if addr_name:
        try:
            return frappe.get_doc("Address", addr_name)
        except frappe.DoesNotExistError:
            pass

    # 2. Dirección default del Customer
    try:
        from frappe.contacts.doctype.address.address import get_default_address
        default_name = get_default_address("Customer", customer_name)
        if default_name:
            return frappe.get_doc("Address", default_name)
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def build_emit_request(doc, tipo_dte: str) -> dict:
    """
    Construye el dict para POST /v2/dte/emit a partir del Sales Invoice y settings.

    Args:
        doc:      Sales Invoice document (frappe.get_doc).
        tipo_dte: "01"=FE, "03"=CCF, "05"=NC, "06"=ND.

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

    if tipo_dte == "06":
        payload.update(_build_nd_extras(doc))

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
        "municipio":           _resolve_municipio(estab.get("municipio")) or "25",
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

    FE: solo nombre + datos opcionales.
    CCF/NC/ND: requiere datos fiscales del Customer y dirección del Address.

    Fuente de datos (en orden de prioridad):
      Identidad fiscal → Customer (sv_nit, sv_nrc, sv_cod_actividad, ...)
      Dirección        → Address.sv_departamento / sv_municipio / address_line1
      Contacto         → Address.email_id / phone  (o Contact / Sales Invoice)
      Fallback legacy  → Customer.sv_direccion_* / sv_correo / sv_telefono
    """
    receptor: dict = {
        "nombre":   doc.get("customer_name") or doc.get("customer") or "Consumidor Final",
        "correo":   doc.get("contact_email") or None,
        "telefono": doc.get("contact_mobile") or None,
    }

    if tipo_dte in ("03", "05", "06") and doc.get("customer"):
        customer = frappe.get_doc("Customer", doc.customer)
        address  = _get_receptor_address(doc, doc.customer)

        # ── Datos fiscales (Customer) ──────────────────────────────────────
        nit = customer.get("sv_nit") or None
        if not nit:
            frappe.throw(f"El Customer '{doc.customer}' no tiene DUI/NIT (sv_nit). Requerido para {tipo_dte}.")

        nrc = customer.get("sv_nrc") or None
        if not nrc:
            frappe.throw(f"El Customer '{doc.customer}' no tiene NRC (sv_nrc). Requerido para {tipo_dte}.")

        cod_act = customer.get("sv_cod_actividad") or None
        if not cod_act:
            frappe.throw(f"El Customer '{doc.customer}' no tiene Código de Actividad (sv_cod_actividad). Requerido para {tipo_dte}.")

        # ── Dirección (Address primero, fallback legacy Customer) ──────────
        dep  = (address.get("sv_departamento")  if address else None) or customer.get("sv_direccion_departamento") or None
        mun  = _resolve_municipio(
               (address.get("sv_municipio")      if address else None) or customer.get("sv_direccion_municipio"))
        comp = (address.get("address_line1")     if address else None) or customer.get("sv_direccion_complemento") or None

        if not (dep and mun and comp):
            src = f"Address '{doc.customer_address}'" if doc.get("customer_address") else "el Customer"
            frappe.throw(
                f"No se encontró dirección DTE completa para '{doc.customer}' en {src}. "
                "Configure el Address del cliente con Departamento, Municipio y Dirección (línea 1)."
            )

        # ── Contacto (Address primero, luego Contact/Sales Invoice, legacy) ─
        correo = (
            (address.get("email_id") if address else None)
            or doc.get("contact_email")
            or customer.get("sv_correo")
            or None
        )
        if not correo:
            frappe.throw(
                f"No se encontró correo electrónico para '{doc.customer}'. "
                "Configure email_id en el Address del cliente. Requerido por schema para {tipo_dte}."
            )

        telefono = (
            (address.get("phone") if address else None)
            or doc.get("contact_mobile")
            or customer.get("sv_telefono")
            or None
        )

        receptor.update({
            "nit":            nit,
            "nrc":            nrc,
            "cod_actividad":  cod_act,
            "desc_actividad": customer.get("sv_desc_actividad") or "",
            "nombre_comercial": customer.get("sv_nombre_comercial") or None,
            "direccion": {
                "departamento": dep,
                "municipio":    mun,
                "complemento":  comp,
            },
            "telefono": telefono,
            "correo":   correo,
        })

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


def _build_nd_extras(doc) -> dict:
    """
    Para ND (tipo 06): resuelve el CCF original via return_against.

    ND solo puede referenciar CCF (tipo 03) en nuestra implementación inicial.
    Lanza frappe.throw si:
    - return_against está vacío
    - El documento relacionado no tiene DTE emitido
    - El tipo del documento relacionado no es CCF
    """
    original_name = doc.get("return_against")
    if not original_name:
        frappe.throw(
            "ND requiere 'return_against' (documento origen). "
            "El Sales Invoice debe ser una nota de débito contra un CCF emitido."
        )

    try:
        original_doc = frappe.get_doc("Sales Invoice", original_name)
    except frappe.DoesNotExistError:
        frappe.throw(f"Documento relacionado '{original_name}' no encontrado.")

    gen_code = original_doc.get("sv_dte_generation_code")
    if not gen_code:
        frappe.throw(
            f"El documento relacionado '{original_name}' no tiene DTE emitido "
            f"(sv_dte_generation_code vacío). Emita el CCF primero."
        )

    raw_tipo = original_doc.get("sv_dte_document_type") or "CCF"
    tipo_original = _DTE_LABEL_TO_CODE.get(raw_tipo, raw_tipo) or "03"
    if tipo_original != "03":
        frappe.throw(
            f"ND solo puede referir a CCF (03). "
            f"El documento '{original_name}' es tipo '{raw_tipo}' → '{tipo_original}'."
        )

    return {
        "documento_relacionado_codigo": gen_code,
        "documento_relacionado_tipo":   tipo_original,
        "documento_relacionado_fecha":  str(original_doc.get("posting_date") or ""),
    }


def _build_nc_extras(doc) -> dict:
    """
    Para NC (tipo 05): resuelve el CCF original via return_against.

    Falla temprano si:
    - return_against está vacío (no es una nota de crédito contra un DTE)
    - El documento relacionado no existe
    - El documento relacionado no tiene DTE emitido (sv_dte_generation_code vacío)
    - El tipo del documento relacionado no es "03" (CCF) o "07" (ND)
    """
    original_name = doc.get("return_against")
    if not original_name:
        frappe.throw(
            "NC requiere 'return_against' (documento origen). "
            "El Sales Invoice debe ser una nota de crédito contra un CCF emitido."
        )

    try:
        original_doc = frappe.get_doc("Sales Invoice", original_name)
    except frappe.DoesNotExistError:
        frappe.throw(f"Documento relacionado '{original_name}' no encontrado.")

    gen_code = original_doc.get("sv_dte_generation_code")
    if not gen_code:
        frappe.throw(
            f"El documento relacionado '{original_name}' no tiene DTE emitido "
            f"(sv_dte_generation_code vacío). Emita el CCF primero."
        )

    raw_tipo = original_doc.get("sv_dte_document_type") or "CCF"
    tipo_original = _DTE_LABEL_TO_CODE.get(raw_tipo, raw_tipo) or "03"
    if tipo_original not in ("03", "07"):
        frappe.throw(
            f"NC solo puede referir a CCF (03) o ND (07). "
            f"El documento '{original_name}' es tipo '{raw_tipo}' → '{tipo_original}'."
        )

    return {
        "documento_relacionado_codigo": gen_code,
        "documento_relacionado_tipo":   tipo_original,
        "documento_relacionado_fecha":  str(original_doc.get("posting_date") or ""),
    }
