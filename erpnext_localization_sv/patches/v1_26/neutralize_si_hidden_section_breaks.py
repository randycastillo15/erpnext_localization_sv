"""
Patch v1.26 — Neutralizar Section Breaks ocultos en header de Sales Invoice.

Causa raíz del fallo del layout 2 columnas (v1_23 a v1_25):
  sv_anulacion_section y sv_contingencia_section son Section Breaks (hidden=1)
  que dividen el header en 3 secciones separadas:

    Sección 1 (customer_section):
      customer, customer_name, campos DTE → todo en col 1, sin column break

    Sección 2 (sv_anulacion_section, label hidden=1):
      sv_anulacion_status solo en col 1  ← nueva sección, reinicia columnas

    Sección 3 (sv_contingencia_section, label hidden=1):
      col 1: vacía (todos los campos hidden)
      sv_si_dte_col_break → col 2: company, posting_date...
      → col 2 parece "invisible" porque col 1 está vacía

Solución:
  Cambiar fieldtype de los Section Breaks custom ocultos a "Data".
  Mismo patrón validado para Column Breaks en v1_20, v1_23, v1_24.
  Para Custom Fields (no estándar) se modifica directamente tabCustom Field.

Layout resultante (una sola sección en el header):
  customer_section:
    Col 1: customer, customer_name
           Tipo DTE, Código Gen, Nº Control, Estado MH, Estado Invalidación
    [sv_si_dte_col_break — after tax_id]
    Col 2: company, company_tax_id, posting_date, posting_time, due_date...
"""


def execute() -> None:
    import frappe

    # ── 1. Neutralizar Section Breaks custom ocultos ───────────────────────────
    #    fieldtype "Data" → ya no crean fronteras de sección en el renderer.
    #    Son Custom Fields: se modifica tabCustom Field directamente.
    for fieldname in [
        "sv_anulacion_section",
        "sv_contingencia_section",
        "sv_dte_section",   # por si existe y está en el header area
    ]:
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, {
                "fieldtype": "Data",
                "hidden": 1,
            })
            frappe.logger().info(f"[v1_26] Neutralizado: {cf_name}")

    frappe.db.commit()

    # ── 2. Forzar recarga para que meta tome los nuevos fieldtype ──────────────
    frappe.reload_doctype("Sales Invoice")
    frappe.clear_cache(doctype="Sales Invoice")

    frappe.logger().info(
        "[v1_26] Section Breaks ocultos neutralizados — "
        "header Sales Invoice en una sola sección, 2 columnas."
    )
