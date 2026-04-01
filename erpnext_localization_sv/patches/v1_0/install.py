"""
Patch de instalación inicial — v1.0
Se ejecuta vía after_install en hooks.py.

Por ahora solo valida el entorno y registra la instalación.
No crea doctypes ni data compleja: eso se hará en patches posteriores
una vez que los DocTypes de configuración fiscal estén definidos.
"""

import frappe


def execute() -> None:
	frappe.logger().info("[erpnext_localization_sv] Iniciando instalación v1.0 ...")

	_check_dependencies()
	_set_defaults()

	frappe.logger().info("[erpnext_localization_sv] Instalación v1.0 completada.")


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _check_dependencies() -> None:
	"""Verifica que las apps requeridas estén instaladas."""
	installed = frappe.get_installed_apps()

	required = ["frappe", "erpnext"]
	missing = [app for app in required if app not in installed]

	if missing:
		frappe.throw(
			f"[erpnext_localization_sv] Faltan apps requeridas: {', '.join(missing)}"
		)

	frappe.logger().info(
		"[erpnext_localization_sv] Dependencias verificadas: %s", required
	)


def _set_defaults() -> None:
	"""Configura Custom Fields y defaults fiscales SV en instalaciones nuevas."""
	from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields

	create_dte_custom_fields()

	# TODO (patch v1_1): crear y poblar "SV DTE Settings"
	# TODO (patch v1_1): asignar country = "El Salvador" y currency = "USD"
