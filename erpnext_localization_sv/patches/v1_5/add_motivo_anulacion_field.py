import frappe


def execute():
    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields
    create_dte_custom_fields()
    frappe.db.commit()
