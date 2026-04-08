"""
Patch v1.6 — Agrega campos Sprint 6 a SV DTE Settings y Sales Invoice:
  - url_verificacion_mh (SV DTE Settings): URL base del portal de verificación MH
  - emitir_al_someter (SV DTE Settings): automatización on_submit
  - sv_dte_qr_url (Sales Invoice Custom Field): URL de verificación generada al emitir
"""

import frappe


def execute():
    # Sincronizar SV DTE Settings con los nuevos campos del JSON
    frappe.reload_doc(
        "ERPNext Localization SV", "doctype", "sv_dte_settings", force=True
    )

    # Crear/actualizar sv_dte_qr_url en Sales Invoice
    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields

    create_dte_custom_fields()

    frappe.db.commit()
