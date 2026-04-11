"""
Custom Fields DTE para Sales Invoice — v1.29

Definición centralizada usada desde:
  - patches/v1_0/add_dte_custom_fields.py  (patch original — sitios existentes)
  - patches/v1_1/update_dte_custom_fields.py (patch v1.1 — añade campos ampliados)
  - patches/v1_4/add_anulacion_contingencia_fields.py (Sprint 4)

v1.29: eliminados 15 campos no utilizados (datos duplicados en SV DTE Document,
Section Breaks neutralizados, campos de contingencia de feature incompleta).
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# insert_after encadena los campos explícitamente dentro de la sección.
# El section break se ancla a "discount_amount", último campo de "Additional Discount".
_DTE_FIELDS = {
    "Sales Invoice": [
        # ── Sección DTE ──────────────────────────────────────────────────────
        {
            "fieldname": "sv_dte_section",
            "fieldtype": "Section Break",
            "label": "DTE El Salvador",
            "collapsible": 1,
            "insert_after": "discount_amount",
        },
        # ── Identificación y configuración ───────────────────────────────────
        {
            "fieldname": "sv_dte_document_type",
            "fieldtype": "Select",
            "label": "Tipo Documental Fiscal",
            "options": "\nFE\nCCF\nNC\nND",
            "no_copy": 1,
            "insert_after": "sv_dte_section",
        },
        {
            "fieldname": "sv_dte_environment",
            "fieldtype": "Select",
            "label": "Ambiente MH",
            "options": "\n00\n01",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_dte_document_type",
        },
        # ── Identificadores DTE ───────────────────────────────────────────────
        {
            "fieldname": "sv_dte_generation_code",
            "fieldtype": "Data",
            "label": "Código de Generación",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "sv_dte_environment",
        },
        {
            "fieldname": "sv_dte_control_number",
            "fieldtype": "Data",
            "label": "Número de Control",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "sv_dte_generation_code",
        },
        # ── Estado MH ─────────────────────────────────────────────────────────
        {
            "fieldname": "sv_estado_mh",
            "fieldtype": "Data",
            "label": "Estado MH",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "sv_dte_control_number",
        },
        # ── Sello y fechas ────────────────────────────────────────────────────
        {
            "fieldname": "sv_sello_recepcion",
            "fieldtype": "Data",
            "label": "Sello de Recepción",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_estado_mh",
        },
        {
            "fieldname": "sv_dte_sent_at",
            "fieldtype": "Datetime",
            "label": "DTE Enviado el",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_sello_recepcion",
        },
        {
            "fieldname": "sv_fecha_procesamiento",
            "fieldtype": "Datetime",
            "label": "Fecha Procesamiento MH",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_dte_sent_at",
        },
        # ── Observaciones ─────────────────────────────────────────────────────
        {
            "fieldname": "sv_observaciones_mh",
            "fieldtype": "Long Text",
            "label": "Observaciones MH",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_fecha_procesamiento",
        },
        # ── URL verificación MH (generada al emitir) ──────────────────────────
        {
            "fieldname": "sv_dte_qr_url",
            "fieldtype": "Data",
            "label": "URL Verificación MH",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_observaciones_mh",
            "description": "URL parametrizada generada al emitir. Usar en 'Ver en Hacienda' y QR del impreso.",
        },
        # ── IVA total DTE (fuente principal para anulación) ───────────────────
        {
            "fieldname": "sv_total_iva",
            "fieldtype": "Currency",
            "label": "IVA Total DTE",
            "read_only": 1,
            "hidden": 1,
            "no_copy": 1,
            "insert_after": "sv_dte_qr_url",
            "description": "IVA calculado al momento de la emisión DTE. Fuente principal para montoIva en anulación.",
        },
        # ── Estado Invalidación ───────────────────────────────────────────────
        {
            "fieldname": "sv_anulacion_status",
            "fieldtype": "Select",
            "label": "Estado Invalidación",
            "options": "\nInvalidado\nRechazado",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "sv_total_iva",
        },
    ]
}


def create_dte_custom_fields() -> None:
    """Crea o actualiza los Custom Fields DTE en Sales Invoice. Idempotente."""
    create_custom_fields(_DTE_FIELDS, ignore_validate=True)
    frappe.logger().info(
        "[erpnext_localization_sv] Custom Fields DTE en Sales Invoice creados/actualizados"
    )
