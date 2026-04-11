"""
Patch v1.23 — Reordena columnas del header de Sales Invoice.

Objetivo:
  Col 1: customer, customer_name → campos DTE (Tipo, Gen, Control, Estado MH, Estado Inv.)
  Col 2: company, posting_date, posting_time, due_date

Técnica:
  1. Mover campos DTE a insert_after: "customer_name" (col 1).
  2. Crear Custom Field sv_si_dte_col_break (Column Break) después del último campo DTE.
  3. Neutralizar column_break1 (estándar) cambiando su fieldtype a "Data" via
     Property Setter — mismo patrón validado en v1_20 (Customer Tax tab).

field_order estándar de Sales Invoice (header):
  customer_section → customer → customer_name → tax_id → company → company_tax_id
  → column_break1 → posting_date → posting_time → due_date → ...

Resultado tras el patch:
  customer_name
  [sv_dte_document_type ... sv_anulacion_status]   ← col 1
  sv_si_dte_col_break                               ← separa columnas
  tax_id → company → company_tax_id                ← col 2
  [column_break1 neutralizado — ya no separa]
  posting_date → posting_time → due_date            ← sigue en col 2
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    # ── 1. Reposicionar campos DTE a col 1 (después de customer_name) ─────────
    visible_chain = [
        ("sv_dte_document_type",   "customer_name"),
        ("sv_dte_generation_code", "sv_dte_document_type"),
        ("sv_dte_control_number",  "sv_dte_generation_code"),
        ("sv_estado_mh",           "sv_dte_control_number"),
        ("sv_anulacion_status",    "sv_estado_mh"),
    ]
    for fieldname, insert_after in visible_chain:
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, {
                "insert_after": insert_after,
                "hidden": 0,
            })

    # ── 2. Crear Column Break custom después del último campo DTE ─────────────
    create_custom_fields({
        "Sales Invoice": [
            {
                "fieldname": "sv_si_dte_col_break",
                "fieldtype": "Column Break",
                "insert_after": "sv_anulacion_status",
            }
        ]
    }, ignore_validate=True)

    # ── 3. Neutralizar column_break1 (estándar) para evitar tercera columna ──
    #    Mismo patrón validado en v1_20: fieldtype → "Data" via Property Setter.
    frappe.db.delete("Property Setter", {
        "doc_type": "Sales Invoice",
        "field_name": "column_break1",
    })
    make_property_setter(
        "Sales Invoice", "column_break1", "fieldtype", "Data", "Select",
        validate_fields_for_doctype=False,
    )
    make_property_setter(
        "Sales Invoice", "column_break1", "hidden", 1, "Check",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()
    frappe.logger().info(
        "[v1_23] Sales Invoice: DTE en col 1, company+fechas en col 2."
    )
