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
# ---------------------------------------------------------------------------
fixtures = [
    {"dt": "SV Actividad Economica"},
]

# ---------------------------------------------------------------------------
# JS personalizado por DocType
# ---------------------------------------------------------------------------
doctype_js = {
    "Sales Invoice":        "public/js/sales_invoice.js",
    "SV DTE Document":      "public/js/sv_dte_document.js",
    "SV DTE Settings":      "public/js/sv_dte_settings.js",
    "Customer":             "public/js/customer_dte.js",
}

doctype_list_js = {
    "SV DTE Document": "public/js/sv_dte_document_list.js",
}

# ---------------------------------------------------------------------------
# Eventos de documento
# on_submit: emisión automática DTE si SV DTE Settings.emitir_al_someter=1.
# Solo activo para FE y CCF. No bloquea el submit en caso de fallo.
# ---------------------------------------------------------------------------
doc_events = {
    "Sales Invoice": {
        "on_submit": "erpnext_localization_sv.overrides.sales_invoice.on_submit",
    },
}

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
