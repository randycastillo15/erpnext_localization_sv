"""
Custom Fields DTE para Customer — v1.2

Campos requeridos para emitir CCF (tipo 03): el receptor debe tener NIT y NRC.
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
            "label": "NIT (DTE)",
            "no_copy": 1,
            "description": "14 dígitos sin guiones — requerido para CCF",
            "insert_after": "sv_dte_section",
        },
        {
            "fieldname": "sv_nrc",
            "fieldtype": "Data",
            "label": "NRC (DTE)",
            "no_copy": 1,
            "description": "Requerido para emitir CCF",
            "insert_after": "sv_nit",
        },
    ]
}


def create_customer_dte_fields() -> None:
    create_custom_fields(_CUSTOMER_DTE_FIELDS, ignore_validate=True)
