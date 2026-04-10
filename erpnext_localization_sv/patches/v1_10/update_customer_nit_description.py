"""
Patch v1.10 — Actualiza descripción del campo sv_nit en Customer.

Antes: "14 dígitos sin guiones — requerido para CCF"
Ahora: "DUI o NIT — 9 dígitos sin guión si es DUI — 14 dígitos sin guiones si es NIT"
"""


def execute() -> None:
    import frappe

    cf_name = "Customer-sv_nit"
    if not frappe.db.exists("Custom Field", cf_name):
        return

    frappe.db.set_value(
        "Custom Field",
        cf_name,
        "description",
        "DUI o NIT — 9 dígitos sin guión si es DUI — 14 dígitos sin guiones si es NIT",
    )
    frappe.db.commit()
