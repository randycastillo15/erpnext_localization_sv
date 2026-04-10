"""
Custom Fields DTE para Address — v1.11

Agrega una sección "DTE El Salvador" al Address estándar de ERPNext con los
campos de dirección fiscal del receptor (departamento y municipio catálogos MH).

Mapeo de campos estándar Address → DTE receptor:
  address_line1  → complemento (detalle de dirección: calle, número, etc.)
  email_id       → correo electrónico receptor (estándar ERPNext)
  phone          → teléfono receptor (estándar ERPNext)
  sv_departamento → departamento CAT-012 (campo custom Link)
  sv_municipio    → municipio CAT-013, filtrado por departamento (campo custom Link)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_ADDRESS_DTE_FIELDS = {
    "Address": [
        {
            "fieldname": "sv_dte_section",
            "fieldtype": "Section Break",
            "label": "DTE El Salvador",
            "collapsible": 1,
            "insert_after": "pincode",
        },
        {
            "fieldname": "sv_departamento",
            "fieldtype": "Link",
            "label": "Departamento",
            "options": "SV Departamento",
            "description": "CAT-012 — requerido para CCF / NC / ND",
            "insert_after": "sv_dte_section",
        },
        {
            "fieldname": "sv_municipio",
            "fieldtype": "Link",
            "label": "Municipio",
            "options": "SV Municipio",
            "description": "CAT-013 — se filtra al seleccionar el departamento",
            "insert_after": "sv_departamento",
        },
    ]
}


def create_address_dte_fields() -> None:
    create_custom_fields(_ADDRESS_DTE_FIELDS, ignore_validate=True)
