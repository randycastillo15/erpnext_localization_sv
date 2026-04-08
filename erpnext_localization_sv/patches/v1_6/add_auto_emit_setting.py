"""
Patch v1.6 — Recarga SV DTE Settings para que el campo
emitir_al_someter (add_qr_settings lo añadió al JSON)
quede registrado en la base de datos.

Idempotente: reload_doc no falla si el campo ya existe.
"""

import frappe


def execute():
    frappe.reload_doc(
        "ERPNext Localization SV", "doctype", "sv_dte_settings", force=True
    )
    frappe.db.commit()
