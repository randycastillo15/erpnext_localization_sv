"""
Patch v1.19 — Corrección layout Tax tab: DTE col 1, tax_id col 2.

El Property Setter insert_after sobre campos estándar no reordena
el campo en el render de Frappe (se ignora). Solución correcta:

  1. Eliminar el Property Setter inefectivo para tax_id (de v1_18)
  2. Crear sv_dte_col_break (Column Break custom, insert_after: sv_desc_actividad)
     → divide la sección en dos columnas desde el Custom Field
  3. Ocultar column_break_21 (estándar) con Property Setter hidden=1
     → evita que cree una tercera columna innecesaria

Layout resultante en Tax tab:
  Col 1: DUI o NIT | NRC | Código Actividad | Descripción Actividad
  Col 2: ID de Impuesto | Categoría de Impuesto | Retención de Impuesto
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields

    # 1. Limpiar Property Setter inefectivo de v1_18
    frappe.db.delete("Property Setter", {
        "doc_type": "Customer",
        "field_name": "tax_id",
        "property": "insert_after",
    })

    # 2. Crear sv_dte_col_break (Column Break después de DTE fields)
    create_customer_dte_fields()

    # 3. Ocultar column_break_21 estándar para evitar tercera columna
    make_property_setter(
        "Customer", "column_break_21", "hidden", 1, "Check",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()
    frappe.logger().info(
        "[v1_19] Tax tab corregido: sv_dte_col_break + column_break_21 oculto."
    )
