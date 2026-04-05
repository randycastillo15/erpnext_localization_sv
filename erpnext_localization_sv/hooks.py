app_name = "erpnext_localization_sv"
app_title = "ERPNext Localization SV"
app_publisher = "Randy Munoz"
app_description = "Localización fiscal y contable para El Salvador"
app_email = "randycastillo15@gmail.com"
app_license = "mit"

# ---------------------------------------------------------------------------
# Apps requeridas
# ---------------------------------------------------------------------------
required_apps = ["frappe", "erpnext"]

# ---------------------------------------------------------------------------
# Instalación
# ---------------------------------------------------------------------------
after_install = "erpnext_localization_sv.patches.v1_0.install.execute"

# ---------------------------------------------------------------------------
# Fixtures
# Los archivos JSON en erpnext_localization_sv/fixtures/ se exportan/importan
# con `bench export-fixtures` / durante migrate.
# Descomentar cuando existan fixtures reales.
# ---------------------------------------------------------------------------
# fixtures = [
# 	{"dt": "Custom Field", "filters": [["module", "=", "ERPNext Localization SV"]]},
# ]

# ---------------------------------------------------------------------------
# JS personalizado por DocType
# ---------------------------------------------------------------------------
doctype_js = {
    "Sales Invoice": "erpnext_localization_sv/public/js/sales_invoice.js",
}

# ---------------------------------------------------------------------------
# Eventos de documento
# Agregar overrides de Sales Invoice, Purchase Invoice, etc. aquí.
# ---------------------------------------------------------------------------
# doc_events = {
# 	"Sales Invoice": {
# 		"on_submit": "erpnext_localization_sv.overrides.sales_invoice.on_submit",
# 	},
# }

# ---------------------------------------------------------------------------
# Tareas programadas
# ---------------------------------------------------------------------------
# scheduler_events = {
# 	"daily": [
# 		"erpnext_localization_sv.tasks.daily",
# 	],
# }

# ---------------------------------------------------------------------------
# Override de métodos whitelisted (reservado para integraciones futuras)
# ---------------------------------------------------------------------------
# override_whitelisted_methods = {}
