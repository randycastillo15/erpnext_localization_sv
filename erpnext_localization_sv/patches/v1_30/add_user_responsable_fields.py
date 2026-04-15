"""
Patch v1.30 — Agrega campos DTE al perfil del usuario.

Campos creados en el doctype User:
  sv_responsable_dte_section   Section Break
  sv_tipo_doc_responsable      Link → SV Tipo Documento (CAT-22)
  sv_num_doc_responsable       Data

El nombre del responsable se toma de user.full_name (ya existe en el perfil de usuario).
"""


def execute() -> None:
    from erpnext_localization_sv.custom_fields.user import create_user_dte_fields

    create_user_dte_fields()
