"""
Patch v1.2 — Agrega campos DTE (sv_nit, sv_nrc) al DocType Customer.

Requeridos para emisión de CCF (tipo 03): el receptor debe tener NIT y NRC.
"""


def execute() -> None:
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields
    create_customer_dte_fields()
