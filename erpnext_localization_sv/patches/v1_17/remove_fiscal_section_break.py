"""
Patch v1.17 — Elimina separadores de la zona fiscal de Customer.

v1.16 creó sv_fiscal_section (Section Break) y sv_fiscal_col_break
(Column Break) para formar dos columnas, pero generaba una línea
divisoria visible que rompía la apariencia integrada del formulario.

Este patch revierte a un flujo de una sola sección continua:
  territory → tax_id → sv_nit → sv_nrc → sv_cod_actividad → sv_desc_actividad
"""


def execute() -> None:
    import frappe
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields

    # 1. Eliminar los campos estructurales del intento anterior
    for cf_name in ("Customer-sv_fiscal_section", "Customer-sv_fiscal_col_break"):
        if frappe.db.exists("Custom Field", cf_name):
            frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True)

    # 2. Eliminar Property Setter de tax_id (revertir a posición estándar)
    frappe.db.delete("Property Setter", {
        "doc_type": "Customer",
        "field_name": "tax_id",
        "property": "insert_after",
    })

    # 3. Actualizar sv_nit → insert_after: tax_id (flujo continuo)
    create_customer_dte_fields()

    frappe.db.commit()
    frappe.logger().info("[v1_17] Section Break fiscal eliminado — una sola sección.")
