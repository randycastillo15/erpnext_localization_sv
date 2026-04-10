"""
Patch v1.10 — Migra campos Departamento y Municipio a Link fields (CAT-012 / CAT-013).

Acciones:
1. Carga fixtures SV Departamento (15) y SV Municipio (45)
2. Actualiza Custom Fields en Customer: sv_direccion_departamento y sv_direccion_municipio Data → Link
3. El establecimiento (SV DTE Establishment) usa DocType nativo: el cambio
   Select→Link se aplica automáticamente durante el model_sync de bench migrate.

Nota sobre datos existentes:
- Customer.sv_direccion_departamento tenía códigos "01"–"14" o "05" directamente.
  SV Departamento.name = código → los valores existentes siguen siendo válidos como Link.
- Customer.sv_direccion_municipio tenía códigos relativos como "25".
  Esos valores quedan como texto en el campo Link hasta que el usuario los actualice
  al nuevo formato "05-25". El payload builder tiene fallback para ambos formatos.
"""


def execute() -> None:
    import frappe
    from frappe.utils.fixtures import sync_fixtures

    # Cargar fixtures de departamentos y municipios
    sync_fixtures(app="erpnext_localization_sv")

    # Actualizar custom fields del Customer
    cf_updates = {
        "Customer-sv_direccion_departamento": {
            "fieldtype": "Link",
            "options": "SV Departamento",
            "description": "CAT-012 — seleccionar departamento",
        },
        "Customer-sv_direccion_municipio": {
            "fieldtype": "Link",
            "options": "SV Municipio",
            "description": "CAT-013 — se filtra según el departamento seleccionado",
        },
    }
    for cf_name, values in cf_updates.items():
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, values)

    frappe.db.commit()
