"""
API whitelisted para SV DTE Document.
"""
import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def refresh_dte_status(dte_doc_name: str) -> dict:
    """
    Consulta el estado MH del DTE y actualiza el SV DTE Document.

    Delega en get_dte_status() (que ya actualiza Sales Invoice y
    llama sync_on_status_check internamente).

    Args:
        dte_doc_name: name del SV DTE Document.
    """
    if not dte_doc_name:
        frappe.throw("dte_doc_name es requerido")

    doc = frappe.get_doc("SV DTE Document", dte_doc_name)

    if not doc.source_docname:
        frappe.throw("Este DTE no tiene documento origen configurado.")

    if doc.source_doctype != "Sales Invoice":
        frappe.throw(
            f"Solo se soporta consulta de estado para Sales Invoice. "
            f"Tipo encontrado: {doc.source_doctype}"
        )

    from erpnext_localization_sv.api.dte import get_dte_status
    result = get_dte_status(doc.source_docname)

    # Asegurar que el SV DTE Document queda actualizado
    # (get_dte_status ya llama sync_on_status_check, pero hacemos set_value
    # directo por si el registro se creó después de la última emisión)
    estado = (result or {}).get("estado")
    if estado:
        frappe.db.set_value("SV DTE Document", dte_doc_name, {
            "mh_status": estado,
            "last_status_check_at": now_datetime(),
        })
        frappe.db.commit()

    return result or {}
