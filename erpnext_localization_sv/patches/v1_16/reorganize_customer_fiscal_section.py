"""
Patch v1.16 — Zona fiscal de Customer: dos columnas.

Layout resultante (después de Territorio):
  ┌─────────────────────────────────────────────────────────┐
  │  Col 1 (DTE)              │  Col 2 (ERPNext estándar)   │
  │  DUI o NIT                │  ID de Impuesto             │
  │  NRC                      │  Categoría de impuesto      │
  │  Código Actividad (Giro)  │  Deshabilitado              │
  │  Descripción Actividad    │  ...                        │
  └─────────────────────────────────────────────────────────┘

Cambios:
  1. Crea Section Break sv_fiscal_section (insert_after: territory)
  2. Crea Column Break sv_fiscal_col_break (insert_after: sv_desc_actividad)
  3. Property Setter: tax_id → insert_after: sv_fiscal_col_break
     (lo mueve al inicio de la segunda columna)
  4. sv_nit → insert_after: sv_fiscal_section (primera posición col 1)
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields

    # 1. Crear/actualizar custom fields (sv_fiscal_section, posiciones sv_nit, sv_fiscal_col_break)
    create_customer_dte_fields()

    # 2. Mover tax_id al inicio de la columna 2 (después del column break DTE)
    make_property_setter(
        "Customer", "tax_id", "insert_after", "sv_fiscal_col_break", "Small Text",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()
    frappe.logger().info("[v1_16] Sección fiscal Customer reorganizada en dos columnas.")
