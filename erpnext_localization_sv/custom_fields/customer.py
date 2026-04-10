"""
Custom Fields DTE para Customer — v1.3

v1.2: sv_nit, sv_nrc (CCF básico)
v1.3: 8 campos adicionales para receptor CCF/NC completo según schema MH fe-ccf-v3.json:
      sv_cod_actividad, sv_desc_actividad, sv_nombre_comercial,
      sv_direccion_departamento, sv_direccion_municipio, sv_direccion_complemento,
      sv_correo, sv_telefono
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_CUSTOMER_DTE_FIELDS = {
    "Customer": [
        {
            "fieldname": "sv_dte_section",
            "fieldtype": "Section Break",
            "label": "DTE El Salvador",
            "collapsible": 1,
            "insert_after": "customer_type",
        },
        {
            "fieldname": "sv_nit",
            "fieldtype": "Data",
            "label": "DUI o NIT",
            "no_copy": 1,
            "description": "9 dígitos sin guión si es DUI — 14 dígitos sin guiones si es NIT",
            "insert_after": "sv_dte_section",
        },
        {
            "fieldname": "sv_nrc",
            "fieldtype": "Data",
            "label": "NRC",
            "no_copy": 1,
            "description": "Requerido para emitir CCF",
            "insert_after": "sv_nit",
        },
        {
            "fieldname": "sv_cod_actividad",
            "fieldtype": "Link",
            "label": "Código Actividad (Giro)",
            "options": "SV Actividad Economica",
            "no_copy": 0,
            "description": "Buscar por código o por nombre del giro — requerido para CCF/NC",
            "insert_after": "sv_nrc",
        },
        {
            "fieldname": "sv_desc_actividad",
            "fieldtype": "Small Text",
            "label": "Descripción Actividad",
            "no_copy": 0,
            "read_only": 1,
            "description": "Se rellena automáticamente al seleccionar el Código Actividad",
            "insert_after": "sv_cod_actividad",
        },
        {
            "fieldname": "sv_nombre_comercial",
            "fieldtype": "Data",
            "label": "Nombre Comercial",
            "no_copy": 0,
            "description": "Nombre comercial del receptor (opcional, nullable en schema)",
            "insert_after": "sv_desc_actividad",
        },
        {
            "fieldname": "sv_col_break_dir",
            "fieldtype": "Column Break",
            "insert_after": "sv_nombre_comercial",
        },
        {
            "fieldname": "sv_direccion_departamento",
            "fieldtype": "Link",
            "label": "Departamento",
            "options": "SV Departamento",
            "no_copy": 0,
            "description": "CAT-012 — seleccionar departamento",
            "insert_after": "sv_col_break_dir",
        },
        {
            "fieldname": "sv_direccion_municipio",
            "fieldtype": "Link",
            "label": "Municipio",
            "options": "SV Municipio",
            "no_copy": 0,
            "description": "CAT-013 — se filtra según el departamento seleccionado",
            "insert_after": "sv_direccion_departamento",
        },
        {
            "fieldname": "sv_direccion_complemento",
            "fieldtype": "Small Text",
            "label": "Dirección Complemento",
            "no_copy": 0,
            "description": "Dirección completa del receptor (calle, número, etc.)",
            "insert_after": "sv_direccion_municipio",
        },
        {
            "fieldname": "sv_correo",
            "fieldtype": "Data",
            "label": "Correo",
            "no_copy": 0,
            "options": "Email",
            "description": "Correo electrónico del receptor — requerido por schema CCF/NC",
            "insert_after": "sv_direccion_complemento",
        },
        {
            "fieldname": "sv_telefono",
            "fieldtype": "Data",
            "label": "Teléfono",
            "no_copy": 0,
            "description": "Teléfono del receptor (opcional, mínimo 8 caracteres)",
            "insert_after": "sv_correo",
        },
    ]
}


def create_customer_dte_fields() -> None:
    create_custom_fields(_CUSTOMER_DTE_FIELDS, ignore_validate=True)
