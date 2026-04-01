"""
Patch v1_0 — Crea Custom Fields DTE en Sales Invoice.

Se ejecuta UNA sola vez por site durante `bench migrate`
(Frappe lo registra en __PatchLog).

Para sitios nuevos, el mismo helper se llama desde
patches/v1_0/install.py vía after_install.
"""

import frappe


def execute() -> None:
	from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields

	frappe.logger().info("[erpnext_localization_sv] Patch add_dte_custom_fields iniciado")
	create_dte_custom_fields()
	frappe.logger().info("[erpnext_localization_sv] Patch add_dte_custom_fields completado")
