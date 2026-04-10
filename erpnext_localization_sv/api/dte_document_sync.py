"""
Sincronización SV DTE Document.

Funciones llamadas desde api/dte.py y api/anulacion.py.
Todas las funciones son tolerantes a fallos — nunca deben interrumpir
el flujo de emisión o invalidación del DTE.

Anti-duplicados: clave natural generation_code (lookup antes de insert).
"""
import frappe
from frappe.utils import now_datetime


def sync_on_emit(
    *,
    source_doctype: str,
    source_docname: str,
    generation_code: str,
    control_number: str | None = None,
    mh_status: str | None = None,
    dte_type_label: str | None = None,
    dte_type_code: str | None = None,
    reception_seal: str | None = None,
    mh_processed_at=None,
    ambiente: str | None = None,
    company: str | None = None,
    customer: str | None = None,
    customer_name: str | None = None,
    mh_verification_url: str | None = None,
) -> None:
    """Crea o actualiza SV DTE Document tras emisión exitosa."""
    if not generation_code:
        return

    existing_name = frappe.db.get_value(
        "SV DTE Document", {"generation_code": generation_code}, "name"
    )

    if existing_name:
        doc = frappe.get_doc("SV DTE Document", existing_name)
    else:
        doc = frappe.new_doc("SV DTE Document")
        doc.source_doctype = source_doctype
        doc.source_docname = source_docname
        doc.generation_code = generation_code
        doc.issued_at = now_datetime()
        doc.issued_by = frappe.session.user

    # Actualizar siempre — refleja el estado más reciente
    if control_number:
        doc.control_number = control_number
    if mh_status:
        doc.mh_status = mh_status
    if dte_type_label:
        doc.dte_type_label = dte_type_label
    if dte_type_code:
        doc.dte_type_code = dte_type_code
    if reception_seal:
        doc.reception_seal = reception_seal
    if mh_processed_at:
        doc.mh_processed_at = mh_processed_at
    if ambiente:
        doc.ambiente = ambiente
    if company:
        doc.company = company
    if customer:
        doc.customer = customer
    if customer_name:
        doc.customer_name = customer_name
    if mh_verification_url:
        doc.mh_verification_url = mh_verification_url
    doc.last_status_check_at = now_datetime()

    if existing_name:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)

    frappe.db.commit()


def sync_on_status_check(*, generation_code: str, mh_status: str) -> None:
    """Actualiza mh_status y last_status_check_at en SV DTE Document.

    El commit es responsabilidad del llamador.
    """
    if not generation_code or not mh_status:
        return

    existing_name = frappe.db.get_value(
        "SV DTE Document", {"generation_code": generation_code}, "name"
    )
    if existing_name:
        frappe.db.set_value("SV DTE Document", existing_name, {
            "mh_status": mh_status,
            "last_status_check_at": now_datetime(),
        })


def sync_on_invalidation(
    *,
    generation_code: str,
    invalidated_at=None,
    replacement_generation_code: str | None = None,
) -> None:
    """Marca el SV DTE Document como invalidado.

    El commit es responsabilidad del llamador.
    """
    if not generation_code:
        return

    existing_name = frappe.db.get_value(
        "SV DTE Document", {"generation_code": generation_code}, "name"
    )
    if existing_name:
        frappe.db.set_value("SV DTE Document", existing_name, {
            "mh_status": "INVALIDADO",
            "is_invalidated": 1,
            "invalidated_at": invalidated_at or now_datetime(),
            "replacement_generation_code": replacement_generation_code or "",
            "last_status_check_at": now_datetime(),
        })
