import frappe


@frappe.whitelist(allow_guest=True)
def ping() -> dict:
	"""Endpoint de salud de la app. No requiere autenticación."""
	from erpnext_localization_sv import __version__

	return {
		"status": "ok",
		"app": "erpnext_localization_sv",
		"version": __version__,
	}
