"""
Patch v1.31 — Establece permisos de DocType para los 4 roles DTE.

Matriz de permisos (aditivos a los roles ERPNext existentes):

  DTE Admin:
    SV DTE Settings       R+W
    SV DTE Establishment  R+W+C+D
    SV DTE Document       R
    SV DTE Log            R
    Catálogos (5)         R+W+C+D

  DTE Responsable:
    SV DTE Document       R
    SV DTE Log            R
    SV DTE Establishment  R
    Catálogos (5)         R

  DTE Operador:
    SV DTE Document       R
    SV DTE Log            R
    SV DTE Establishment  R
    Catálogos (5)         R

  DTE Auditor:
    SV DTE Document       R + export
    SV DTE Log            R + export
    SV DTE Establishment  R
    Catálogos (5)         R

Los permisos de System Manager y Accounts Manager preexistentes
se conservan — este patch solo AGREGA entradas nuevas.
"""

_ROLE_PERMISSIONS = {
    "DTE Admin": {
        "SV DTE Settings":       {"read": 1, "write": 1},
        "SV DTE Establishment":  {"read": 1, "write": 1, "create": 1, "delete": 1},
        "SV DTE Document":       {"read": 1},
        "SV DTE Log":            {"read": 1},
        "SV Tipo Documento":     {"read": 1, "write": 1, "create": 1, "delete": 1},
        "SV Actividad Economica":{"read": 1, "write": 1, "create": 1, "delete": 1},
        "SV Departamento":       {"read": 1, "write": 1, "create": 1, "delete": 1},
        "SV Municipio":          {"read": 1, "write": 1, "create": 1, "delete": 1},
        "SV Distrito":           {"read": 1, "write": 1, "create": 1, "delete": 1},
    },
    "DTE Responsable": {
        "SV DTE Document":       {"read": 1},
        "SV DTE Log":            {"read": 1},
        "SV DTE Establishment":  {"read": 1},
        "SV Tipo Documento":     {"read": 1},
        "SV Actividad Economica":{"read": 1},
        "SV Departamento":       {"read": 1},
        "SV Municipio":          {"read": 1},
        "SV Distrito":           {"read": 1},
    },
    "DTE Operador": {
        "SV DTE Document":       {"read": 1},
        "SV DTE Log":            {"read": 1},
        "SV DTE Establishment":  {"read": 1},
        "SV Tipo Documento":     {"read": 1},
        "SV Actividad Economica":{"read": 1},
        "SV Departamento":       {"read": 1},
        "SV Municipio":          {"read": 1},
        "SV Distrito":           {"read": 1},
    },
    "DTE Auditor": {
        "SV DTE Document":       {"read": 1, "export": 1},
        "SV DTE Log":            {"read": 1, "export": 1},
        "SV DTE Establishment":  {"read": 1},
        "SV Tipo Documento":     {"read": 1},
        "SV Actividad Economica":{"read": 1},
        "SV Departamento":       {"read": 1},
        "SV Municipio":          {"read": 1},
        "SV Distrito":           {"read": 1},
    },
}

# Tipos de permiso soportados por frappe.permissions.update_permission_property
_ALL_PTYPES = (
    "read", "write", "create", "delete",
    "submit", "cancel", "amend",
    "report", "export", "import",
    "share", "print", "email",
)


def execute() -> None:
    import frappe
    import frappe.permissions

    for role, doctypes in _ROLE_PERMISSIONS.items():
        for doctype, perms in doctypes.items():
            # Verificar si ya existe una entrada DocPerm para este doctype+role
            existing = frappe.db.get_value(
                "DocPerm",
                {"parent": doctype, "role": role, "permlevel": 0},
                "name",
            )
            if not existing:
                frappe.permissions.add_permission(doctype, role, 0)

            # Primero poner a 0 todos los tipos (para partir de estado limpio)
            for ptype in _ALL_PTYPES:
                try:
                    frappe.permissions.update_permission_property(
                        doctype, role, 0, ptype, 0
                    )
                except Exception:
                    pass  # Algunos tipos no aplican a todos los doctypes

            # Luego activar solo los definidos en la matriz
            for ptype, val in perms.items():
                try:
                    frappe.permissions.update_permission_property(
                        doctype, role, 0, ptype, val
                    )
                except Exception as exc:
                    frappe.logger().warning(
                        "[erpnext_localization_sv] No se pudo actualizar permiso "
                        "%s.%s.%s: %s", doctype, role, ptype, exc
                    )

    frappe.db.commit()
    frappe.logger().info(
        "[erpnext_localization_sv] Permisos DTE configurados para %d roles.",
        len(_ROLE_PERMISSIONS),
    )
