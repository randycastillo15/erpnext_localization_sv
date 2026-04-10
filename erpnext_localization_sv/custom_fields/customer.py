"""
Custom Fields DTE para Customer — v1.11

v1.2:  sv_nit, sv_nrc (CCF básico)
v1.3:  dirección y contacto en Customer (directo)
v1.11: MIGRACIÓN — dirección y contacto se mueven a Address estándar.
       Customer conserva solo datos fiscales/identitarios del receptor.
       Los campos de dirección/contacto quedan hidden=1 (datos preservados
       en DB como fallback para documentos emitidos antes de la migración).

Campos activos en Customer:
  sv_nit              DUI o NIT del receptor
  sv_nrc              NRC del receptor
  sv_cod_actividad    Código de actividad económica (Link CAT-019)
  sv_desc_actividad   Descripción (auto-rellenada, read-only)
  sv_nombre_comercial Nombre comercial (opcional)

Campos legacy hidden (fallback):
  sv_direccion_departamento, sv_direccion_municipio,
  sv_direccion_complemento, sv_correo, sv_telefono
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_CUSTOMER_DTE_FIELDS = {
    "Customer": [
        # ── Sección activa ──────────────────────────────────────────────────
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
            "description": "Nombre comercial del receptor (opcional)",
            "insert_after": "sv_desc_actividad",
        },
        # ── Campos legacy — hidden, datos preservados para fallback ────────
        # La dirección y contacto del receptor viven ahora en Address estándar.
        # Estos campos se mantienen ocultos para compatibilidad con documentos
        # emitidos antes de la migración v1.11.
        {
            "fieldname": "sv_col_break_dir",
            "fieldtype": "Column Break",
            "hidden": 1,
            "insert_after": "sv_nombre_comercial",
        },
        {
            "fieldname": "sv_direccion_departamento",
            "fieldtype": "Link",
            "label": "Departamento (legacy)",
            "options": "SV Departamento",
            "hidden": 1,
            "no_copy": 0,
            "insert_after": "sv_col_break_dir",
        },
        {
            "fieldname": "sv_direccion_municipio",
            "fieldtype": "Link",
            "label": "Municipio (legacy)",
            "options": "SV Municipio",
            "hidden": 1,
            "no_copy": 0,
            "insert_after": "sv_direccion_departamento",
        },
        {
            "fieldname": "sv_direccion_complemento",
            "fieldtype": "Small Text",
            "label": "Dirección Complemento (legacy)",
            "hidden": 1,
            "no_copy": 0,
            "insert_after": "sv_direccion_municipio",
        },
        {
            "fieldname": "sv_correo",
            "fieldtype": "Data",
            "label": "Correo (legacy)",
            "hidden": 1,
            "no_copy": 0,
            "options": "Email",
            "insert_after": "sv_direccion_complemento",
        },
        {
            "fieldname": "sv_telefono",
            "fieldtype": "Data",
            "label": "Teléfono (legacy)",
            "hidden": 1,
            "no_copy": 0,
            "insert_after": "sv_correo",
        },
    ]
}


def create_customer_dte_fields() -> None:
    create_custom_fields(_CUSTOMER_DTE_FIELDS, ignore_validate=True)
