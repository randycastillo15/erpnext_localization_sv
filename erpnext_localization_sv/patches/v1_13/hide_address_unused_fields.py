"""
Patch v1.13 — Oculta campos del formulario Address que no se usan en El Salvador.

Usa Property Setters (mecanismo estándar Frappe) para sobreescribir propiedades
de campos estándar de ERPNext sin modificar el core.

Campos ocultados:
  - address_line2  (Dirección línea 2)
  - city           (Ciudad / Provincia) — también se quita reqd para evitar errores
  - county         (Condado)
  - state          (Estado / Provincia)
"""


def execute() -> None:
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    hidden_fields = ["address_line2", "city", "county", "state"]
    for fieldname in hidden_fields:
        make_property_setter("Address", fieldname, "hidden", 1, "Check",
                             validate_fields_for_doctype=False)

    # city es reqd en ERPNext estándar — quitarlo para no bloquear el guardado
    make_property_setter("Address", "city", "reqd", 0, "Check",
                         validate_fields_for_doctype=False)

    import frappe
    frappe.db.commit()
    frappe.logger().info("[v1_13] Campos Address ocultados: %s", hidden_fields)
