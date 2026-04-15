"""
Custom Fields DTE para User — v1.30

Agrega dos campos al perfil del usuario para identificarlo como
responsable técnico en invalidaciones y contingencias DTE.

El nombre del responsable se toma de user.full_name (ya existe en el perfil).
Solo se agregan tipo y número de documento.

Layout en el formulario de Usuario (pestaña principal, debajo de language):
  sv_responsable_dte_section   Section Break
  sv_tipo_doc_responsable      Link → SV Tipo Documento (CAT-22, con descripción)
  sv_num_doc_responsable       Data

Uso en API:
  user_doc = frappe.get_doc("User", frappe.session.user)
  nombre_responsable  = user_doc.full_name
  tipo_doc_responsable = user_doc.sv_tipo_doc_responsable   # "36","13","02","03","37"
  num_doc_responsable  = user_doc.sv_num_doc_responsable
"""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

_USER_DTE_FIELDS = {
    "User": [
        {
            "fieldname": "sv_responsable_dte_section",
            "fieldtype": "Section Break",
            "label": "Responsable DTE (Invalidaciones / Contingencias)",
            "insert_after": "language",
        },
        {
            "fieldname": "sv_tipo_doc_responsable",
            "fieldtype": "Link",
            "label": "Tipo Doc Responsable",
            "options": "SV Tipo Documento",
            "description": "Tipo de documento de identificación (CAT-22 MH). El nombre se toma del campo 'Nombre completo' del perfil.",
            "insert_after": "sv_responsable_dte_section",
        },
        {
            "fieldname": "sv_num_doc_responsable",
            "fieldtype": "Data",
            "label": "Núm. Doc Responsable",
            "description": "Número de documento según el tipo seleccionado (mín. 3, máx. 20 caracteres).",
            "insert_after": "sv_tipo_doc_responsable",
        },
    ]
}


def create_user_dte_fields() -> None:
    create_custom_fields(_USER_DTE_FIELDS, ignore_validate=True)
