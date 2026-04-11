"""
Patch v1.20 — Neutraliza column_break_21 para lograr 2 columnas exactas en Tax tab.

El problema:
  hidden=1 en un Column Break no lo suprime en el render de Frappe — el
  Column Break sigue creando una nueva columna aunque esté oculto, generando
  3 columnas: [DTE] | [tax_id] | [tax_cat + tax_with].

Solución:
  Cambiar el fieldtype de column_break_21 de "Column Break" a "Data" via
  Property Setter. Al dejar de ser un Column Break, Frappe no lo procesa
  como separador de columnas. Se oculta además con hidden=1.

Layout resultante (2 columnas exactas):
  Col 1: DUI o NIT | NRC | Código Actividad | Descripción Actividad
  Col 2: ID de Impuesto | Categoría de Impuesto | Retención de Impuesto
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    # Reemplazar el PS de hidden (v1_19) por cambio de fieldtype
    frappe.db.delete("Property Setter", {
        "doc_type": "Customer",
        "field_name": "column_break_21",
    })

    # Cambiar fieldtype: Column Break → Data (deja de ser separador de columnas)
    make_property_setter(
        "Customer", "column_break_21", "fieldtype", "Data", "Select",
        validate_fields_for_doctype=False,
    )
    # Ocultar el campo resultante
    make_property_setter(
        "Customer", "column_break_21", "hidden", 1, "Check",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()
    frappe.logger().info(
        "[v1_20] column_break_21 neutralizado — Tax tab con 2 columnas exactas."
    )
