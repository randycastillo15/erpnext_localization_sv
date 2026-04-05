"""
Patch v1_5b: corregir terminología sv_anulacion_status.

- Actualiza las opciones del campo: "Anulado" → "Invalidado"
- Migra registros existentes con valor "Anulado" → "Invalidado"
"""
import frappe


def execute():
    # 1. Actualizar definición del campo (opciones)
    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields
    create_dte_custom_fields()

    # 2. Migrar registros existentes en Sales Invoice
    frappe.db.sql(
        "UPDATE `tabSales Invoice` SET sv_anulacion_status='Invalidado' WHERE sv_anulacion_status='Anulado'"
    )

    frappe.db.commit()
