"""
Patch v1.24 — Corrige layout de 2 columnas en Sales Invoice header.

Problemas del patch v1_23:
  1. idx=0 en todos los custom fields — frappe.db.set_value no recalcula idx,
     lo que hace que el chain de insert_after no se resuelva correctamente.
  2. column_break_14 activo crea una tercera columna (33% cada col),
     haciendo que col 2 quede invisible o muy estrecha.

Solución:
  1. Recrear sv_si_dte_col_break y los 5 campos DTE via create_custom_fields
     (asigna idx correctamente y respeta la cadena insert_after).
  2. Neutralizar column_break_14 con el mismo patrón validado en v1_20 y v1_23.
  3. frappe.reload_doctype("Sales Invoice") para forzar recálculo de idx.

Layout resultante:
  Col 1: customer, customer_name
          → Tipo DTE, Código Gen, Número Control, Estado MH, Estado Inv.
  [sv_si_dte_col_break]
  Col 2: tax_id, company, company_tax_id, posting_date, posting_time, due_date
  [column_break1 neutralizado — no crea col 3]
  [column_break_14 neutralizado — no crea col 3]
"""


def execute() -> None:
    import frappe
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    # ── 1. Recrear los campos DTE y el Column Break via create_custom_fields ──
    #    Esto asigna idx correctamente y respeta la cadena insert_after.
    create_custom_fields({
        "Sales Invoice": [
            {
                "fieldname": "sv_dte_document_type",
                "fieldtype": "Select",
                "label": "Tipo DTE",
                "options": "\nFE\nCCF\nNC\nND",
                "no_copy": 1,
                "hidden": 0,
                "insert_after": "customer_name",
            },
            {
                "fieldname": "sv_dte_generation_code",
                "fieldtype": "Data",
                "label": "C\u00f3digo de Generaci\u00f3n",
                "read_only": 1,
                "no_copy": 1,
                "hidden": 0,
                "insert_after": "sv_dte_document_type",
            },
            {
                "fieldname": "sv_dte_control_number",
                "fieldtype": "Data",
                "label": "N\u00famero de Control",
                "read_only": 1,
                "no_copy": 1,
                "hidden": 0,
                "insert_after": "sv_dte_generation_code",
            },
            {
                "fieldname": "sv_estado_mh",
                "fieldtype": "Data",
                "label": "Estado MH",
                "read_only": 1,
                "no_copy": 1,
                "hidden": 0,
                "insert_after": "sv_dte_control_number",
            },
            {
                "fieldname": "sv_anulacion_status",
                "fieldtype": "Select",
                "label": "Estado Invalidaci\u00f3n",
                "options": "\nInvalidado\nRechazado",
                "read_only": 1,
                "no_copy": 1,
                "hidden": 0,
                "insert_after": "sv_estado_mh",
            },
            {
                "fieldname": "sv_si_dte_col_break",
                "fieldtype": "Column Break",
                "hidden": 0,
                "insert_after": "sv_anulacion_status",
            },
        ]
    }, ignore_validate=True)

    # ── 2. Neutralizar column_break_14 — evita tercera columna vacía ──────────
    frappe.db.delete("Property Setter", {
        "doc_type": "Sales Invoice",
        "field_name": "column_break_14",
    })
    make_property_setter(
        "Sales Invoice", "column_break_14", "fieldtype", "Data", "Select",
        validate_fields_for_doctype=False,
    )
    make_property_setter(
        "Sales Invoice", "column_break_14", "hidden", 1, "Check",
        validate_fields_for_doctype=False,
    )

    frappe.db.commit()

    # ── 3. Forzar recálculo de idx para resolver el chain de insert_after ─────
    frappe.reload_doctype("Sales Invoice")
    frappe.clear_cache(doctype="Sales Invoice")

    frappe.logger().info(
        "[v1_24] Sales Invoice: 2 columnas corregidas — DTE en col 1, "
        "company+fechas en col 2."
    )
