"""
Patch v1.30 — Crea el rol 'DTE Responsable'.

Los usuarios con este rol pueden ejecutar invalidaciones y contingencias DTE.
Sin este rol, las funciones anular_dte() y emit_contingencia() rechazan la solicitud.
"""


def execute() -> None:
    import frappe

    if not frappe.db.exists("Role", "DTE Responsable"):
        role = frappe.new_doc("Role")
        role.role_name = "DTE Responsable"
        role.desk_access = 1
        role.insert(ignore_permissions=True)

    frappe.db.commit()
