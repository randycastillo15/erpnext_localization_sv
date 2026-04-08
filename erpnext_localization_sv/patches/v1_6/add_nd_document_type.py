"""
Patch v1.6 — Agrega "ND" como opción de sv_dte_document_type en Sales Invoice.

Idempotente: create_dte_custom_fields usa upsert (insert_if_not_exists no aplica —
frappe actualiza el campo si ya existe).
"""

import frappe


def execute():
    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields

    create_dte_custom_fields()
    frappe.db.commit()
