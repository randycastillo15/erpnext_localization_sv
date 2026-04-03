"""
Patch v1_1 — Actualiza Custom Fields DTE en Sales Invoice.

Añade los campos ampliados v1.1:
  sv_dte_document_type, sv_dte_environment, sv_dte_generation_code,
  sv_dte_control_number, sv_estado_mh, sv_sello_recepcion,
  sv_fecha_procesamiento, sv_dte_last_payload, sv_observaciones_mh,
  sv_codigo_msg, sv_clasifica_msg

Nota: sv_dte_uuid se MANTIENE por compatibilidad temporal.
      Su eliminación se realizará en un patch posterior.
"""

import frappe


def execute() -> None:
    frappe.logger().info("[erpnext_localization_sv] Patch v1_1 update_dte_custom_fields iniciado")

    from erpnext_localization_sv.custom_fields.sales_invoice import create_dte_custom_fields
    create_dte_custom_fields()

    frappe.logger().info("[erpnext_localization_sv] Patch v1_1 update_dte_custom_fields completado")
