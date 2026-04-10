"""
Custom Fields DTE para Customer — v1.15

Integración inline — sin sección separada "DTE El Salvador".

Layout en el formulario:
  Columna izquierda (basic_info):
    customer_name → sv_nombre_comercial → gender → ...

  Columna derecha (después de column_break0):
    account_manager → customer_type (*) → customer_group → territory →
    tax_id → sv_nit → sv_nrc → sv_cod_actividad → sv_desc_actividad → ...

  (*) customer_type se reposiciona via Property Setter en patch v1_14.

Campos activos:
  sv_nombre_comercial  Nombre comercial — justo después de customer_name
  sv_nit               DUI o NIT — después de tax_id
  sv_nrc               NRC — después de sv_nit
  sv_cod_actividad     Código de actividad económica (Link CAT-019)
  sv_desc_actividad    Descripción (auto-rellenada, read-only)

Los campos legacy de dirección/contacto fueron eliminados en v1.15.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_CUSTOMER_DTE_FIELDS = {
    "Customer": [
        # ── Nombre comercial — columna izquierda, justo bajo el nombre ─────
        {
            "fieldname": "sv_nombre_comercial",
            "fieldtype": "Data",
            "label": "Nombre Comercial",
            "no_copy": 0,
            "description": "Nombre comercial del receptor (opcional)",
            "insert_after": "customer_name",
        },
        # ── Datos fiscales — columna derecha, zona fiscal ──────────────────
        {
            "fieldname": "sv_nit",
            "fieldtype": "Data",
            "label": "DUI o NIT",
            "no_copy": 1,
            "description": "9 dígitos sin guión si es DUI — 14 dígitos sin guiones si es NIT",
            "insert_after": "tax_id",
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
    ]
}


def create_customer_dte_fields() -> None:
    create_custom_fields(_CUSTOMER_DTE_FIELDS, ignore_validate=True)
