"""
Patch v1.25 — Ancla sv_si_dte_col_break a campo estándar para layout confiable.

Problema detectado en v1_23/v1_24:
  - sv_dte_environment.insert_after = "sv_dte_document_type" CONFLICTA con
    sv_dte_generation_code.insert_after = "sv_dte_document_type".
  - Múltiples campos ocultos compiten en el mismo insert_after target,
    generando orden arbitrario en el chain de custom fields.
  - Anclar sv_si_dte_col_break a un campo custom (sv_anulacion_status)
    no es confiable cuando hay conflictos de idx=0.

Solución:
  Anclar sv_si_dte_col_break a un campo ESTÁNDAR con posición fija
  en el field_order de Sales Invoice:

    field_order:  ... tax_id(5) → company(6) → company_tax_id(7)
                      → [col_break1 neutralizado] → posting_date(9) ...

  sv_si_dte_col_break.insert_after = "tax_id"
  → Column Break se inserta entre tax_id y company, garantizado.

  Adicionalmente, ocultar tax_id en Sales Invoice (se usa sv_nit en
  el formulario de Customer para el DTE). Esto deja col 1 sin tax_id
  visible y col 2 empezando directamente en company.

Layout resultante:
  Col 1: customer, customer_name
          Tipo DTE / Código Gen / Número Control / Estado MH / Estado Inv.
  [sv_si_dte_col_break — after tax_id, guaranteed position]
  Col 2: Empresa (company), Fecha Contabilización, Hora, Fecha Pago
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    # ── 1. Reanchar sv_si_dte_col_break a "tax_id" (campo estándar fijo) ─────
    cf_name = "Sales Invoice-sv_si_dte_col_break"
    if frappe.db.exists("Custom Field", cf_name):
        frappe.db.set_value("Custom Field", cf_name, "insert_after", "tax_id")

    # ── 2. Ocultar tax_id en Sales Invoice — usamos sv_nit en Customer ────────
    frappe.db.delete("Property Setter", {
        "doc_type": "Sales Invoice",
        "field_name": "tax_id",
    })
    make_property_setter(
        "Sales Invoice", "tax_id", "hidden", 1, "Check",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()

    # ── 3. Limpiar caché del DocType ──────────────────────────────────────────
    frappe.reload_doctype("Sales Invoice")
    frappe.clear_cache(doctype="Sales Invoice")

    frappe.logger().info(
        "[v1_25] sv_si_dte_col_break anclado a 'tax_id' — "
        "Col 1: DTE, Col 2: company + fechas."
    )
