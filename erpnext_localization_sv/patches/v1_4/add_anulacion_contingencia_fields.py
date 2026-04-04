"""
Patch v1.4 — Agrega campos de Anulación y Contingencia DTE al Sales Invoice.

Nuevos campos en Sales Invoice:
  sv_total_iva — IVA calculado en el DTE (fuente principal para montoIva en anulación)
  sv_anulacion_status, sv_anulacion_tipo, sv_anulacion_sello,
  sv_anulacion_fecha, sv_anulacion_codigo_generacion_reemplazo
  sv_contingencia_event_uuid, sv_contingencia_tipo, sv_contingencia_sello

Nota: Los campos del Responsable (sv_nombre_responsable, etc.) se agregan directamente
al Doctype SV DTE Settings vía el JSON del Doctype (no require patch de custom fields).
"""


def execute():
    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields
    create_dte_custom_fields()
