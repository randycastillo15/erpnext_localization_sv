"""
Patch v1.31 — Crea los roles del sistema DTE El Salvador.

Roles creados (DTE Responsable ya existe desde v1_30):
  DTE Admin     — configura SV DTE Settings, establecimientos y catálogos
  DTE Operador  — emite DTEs y consulta estados MH
  DTE Auditor   — lectura y exportación de documentos y logs DTE (sin escritura)

Roles aditivos: el usuario necesita su rol ERPNext normal MÁS el rol DTE.
Ejemplo: Accounts User + DTE Operador = puede emitir DTEs.

El usuario Administrator recibe DTE Admin + DTE Operador automáticamente.
(DTE Responsable ya asignado en patch v1_30.)
"""


def execute() -> None:
    import frappe

    new_roles = ["DTE Admin", "DTE Operador", "DTE Auditor"]
    for role_name in new_roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.insert(ignore_permissions=True)
            frappe.logger().info("[erpnext_localization_sv] Rol creado: %s", role_name)

    frappe.db.commit()

    # Asignar DTE Admin + DTE Operador al usuario Administrator
    # DTE Responsable ya fue asignado en patch v1_30
    admin_roles_to_assign = ["DTE Admin", "DTE Operador"]
    for role_name in admin_roles_to_assign:
        existing = frappe.db.sql(
            "SELECT name FROM `tabHas Role` WHERE parent=%s AND role=%s LIMIT 1",
            ("Administrator", role_name),
        )
        if not existing:
            frappe.db.sql(
                "INSERT INTO `tabHas Role` (name, parent, parenttype, parentfield, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (frappe.generate_hash()[:10], "Administrator", "User", "roles", role_name),
            )
            frappe.logger().info(
                "[erpnext_localization_sv] Rol %s asignado a Administrator", role_name
            )

    frappe.db.commit()
