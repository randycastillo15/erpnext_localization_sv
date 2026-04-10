"""
Custom Fields DTE para Address — v1.11

Agrega una sección "DTE El Salvador" al Address estándar de ERPNext con los
campos de dirección fiscal del receptor (departamento y municipio catálogos MH).

Integración inline en el formulario Address estándar (sin sección separada):
  address_line1  → complemento / calle / detalle (estándar ERPNext)
  sv_departamento → departamento CAT-012 — insertado después de address_line1
  sv_municipio    → municipio CAT-013 — insertado después de sv_departamento
  city           → campo estándar que sigue (Ciudad)
  country        → campo estándar (País)
  email_id       → correo electrónico receptor (estándar ERPNext)
  phone          → teléfono receptor (estándar ERPNext)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_ADDRESS_DTE_FIELDS = {
    "Address": [
        {
            "fieldname": "sv_departamento",
            "fieldtype": "Link",
            "label": "Departamento",
            "options": "SV Departamento",
            "in_list_view": 0,
            "insert_after": "address_line1",
        },
        {
            "fieldname": "sv_municipio",
            "fieldtype": "Link",
            "label": "Municipio",
            "options": "SV Municipio",
            "in_list_view": 0,
            "insert_after": "sv_departamento",
        },
        {
            "fieldname": "sv_distrito",
            "fieldtype": "Link",
            "label": "Distrito",
            "options": "SV Distrito",
            "in_list_view": 0,
            "insert_after": "sv_municipio",
        },
    ]
}


def create_address_dte_fields() -> None:
    create_custom_fields(_ADDRESS_DTE_FIELDS, ignore_validate=True)
