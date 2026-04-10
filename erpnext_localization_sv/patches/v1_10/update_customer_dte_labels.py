"""
Patch v1.10 — Limpia labels de campos DTE en Customer.

- Quita sufijo "(DTE)" de todos los labels de la sección DTE El Salvador.
- Renombra "NIT (DTE)" → "DUI o NIT".
- Ajusta description de sv_nit.
"""


_FIELD_UPDATES = {
    "Customer-sv_nit": {
        "label": "DUI o NIT",
        "description": "9 dígitos sin guión si es DUI — 14 dígitos sin guiones si es NIT",
    },
    "Customer-sv_nrc":                 {"label": "NRC"},
    "Customer-sv_cod_actividad":       {"label": "Código Actividad"},
    "Customer-sv_desc_actividad":      {"label": "Descripción Actividad"},
    "Customer-sv_nombre_comercial":    {"label": "Nombre Comercial"},
    "Customer-sv_direccion_departamento": {"label": "Departamento"},
    "Customer-sv_direccion_municipio": {"label": "Municipio"},
    "Customer-sv_direccion_complemento": {"label": "Dirección Complemento"},
    "Customer-sv_correo":              {"label": "Correo"},
    "Customer-sv_telefono":            {"label": "Teléfono"},
}


def execute() -> None:
    import frappe

    for cf_name, values in _FIELD_UPDATES.items():
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, values)

    frappe.db.commit()
