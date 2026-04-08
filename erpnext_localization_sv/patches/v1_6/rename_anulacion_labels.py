"""
Patch v1.6 — Normaliza labels de "Anulación" → "Invalidación" en campos visibles.

Los fieldnames (sv_anulacion_*), la función anular_dte() y el endpoint /anular
NO cambian. Solo se actualizan los labels visibles al operador.
"""

import frappe


def execute():
    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields

    create_dte_custom_fields()

    # Sincronizar el label de la sección Responsable en SV DTE Settings
    frappe.reload_doc(
        "ERPNext Localization SV", "doctype", "sv_dte_settings", force=True
    )

    frappe.db.commit()
