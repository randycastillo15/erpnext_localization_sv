"""
Patch v1.18 — Tax tab de Customer: tax_id a columna derecha.

El field_order del Customer DocType define el Tax tab así:
  tax_tab
    taxation_section   ← Section Break invisible
    tax_id             ← col izquierda (actualmente)
    column_break_21    ← separador de columnas
    tax_category       ← col derecha
    tax_withholding_category

Objetivo:
  Col izquierda: sv_nit, sv_nrc, sv_cod_actividad, sv_desc_actividad (solo DTE)
  Col derecha:   tax_id, tax_category, tax_withholding_category

Cambios:
  1. sv_nit → insert_after: "taxation_section" (primer campo col izquierda)
  2. Property Setter: tax_id → insert_after: "column_break_21" (col derecha)
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields

    # 1. Actualizar sv_nit.insert_after → "taxation_section"
    create_customer_dte_fields()

    # 2. Mover tax_id al inicio de la columna derecha
    make_property_setter(
        "Customer", "tax_id", "insert_after", "column_break_21", "Small Text",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()
    frappe.logger().info(
        "[v1_18] tax_id movido a col derecha del Tax tab — DTE queda en col izquierda."
    )
