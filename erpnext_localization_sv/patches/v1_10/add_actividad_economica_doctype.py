"""
Patch v1.10 — Migra campo Código Actividad (CAT-019) a Link field.

Acciones:
1. Actualiza Custom Field Customer-sv_cod_actividad: Data → Link a SV Actividad Economica
2. Marca sv_desc_actividad como read_only (se auto-rellena vía JS)
3. Carga el fixture sv_actividad_economica.json con los 774 códigos CAT-019
"""


def execute() -> None:
    import frappe
    from frappe.utils.fixtures import sync_fixtures

    # 1. Actualizar custom fields del Customer
    cf_updates = {
        "Customer-sv_cod_actividad": {
            "fieldtype": "Link",
            "options": "SV Actividad Economica",
            "label": "Código Actividad (Giro)",
            "description": "Buscar por código o por nombre del giro — requerido para CCF/NC",
        },
        "Customer-sv_desc_actividad": {
            "read_only": 1,
            "description": "Se rellena automáticamente al seleccionar el Código Actividad",
        },
    }
    for cf_name, values in cf_updates.items():
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, values)

    frappe.db.commit()

    # 2. Cargar el fixture de SV Actividad Economica
    sync_fixtures(app="erpnext_localization_sv")
