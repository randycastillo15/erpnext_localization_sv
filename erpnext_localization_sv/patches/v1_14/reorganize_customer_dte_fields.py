"""
Patch v1.14 — Integra campos DTE de Customer inline, sin sección separada.

Cambios:
  1. Elimina el Section Break "DTE El Salvador" (Customer-sv_dte_section)
  2. Reposiciona los custom fields DTE en el layout estándar de Customer:
       sv_nombre_comercial → después de customer_name (columna izquierda)
       sv_nit / sv_nrc / sv_cod_actividad / sv_desc_actividad → después de tax_id
  3. Property Setter: customer_type pasa a columna derecha, justo antes de
     customer_group (insert_after: account_manager)
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields

    # 1. Eliminar la sección DTE (ya no se usa)
    if frappe.db.exists("Custom Field", "Customer-sv_dte_section"):
        frappe.delete_doc("Custom Field", "Customer-sv_dte_section",
                          ignore_permissions=True)

    # 2. Actualizar posiciones de los custom fields DTE
    create_customer_dte_fields()

    # 3. Mover customer_type justo antes de customer_group
    #    (de columna izquierda a columna derecha, tras account_manager)
    make_property_setter(
        "Customer", "customer_type", "insert_after", "account_manager", "Small Text",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()
    frappe.logger().info("[v1_14] Layout Customer DTE reorganizado — sección eliminada.")
