"""
Patch v1.3 — Agrega campos DTE adicionales al Customer para CCF/NC completo.

Nuevos campos: sv_cod_actividad, sv_desc_actividad, sv_nombre_comercial,
sv_direccion_departamento, sv_direccion_municipio, sv_direccion_complemento,
sv_correo, sv_telefono.

Requeridos por schema MH fe-ccf-v3.json para el bloque receptor.
"""


def execute():
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields
    create_customer_dte_fields()
