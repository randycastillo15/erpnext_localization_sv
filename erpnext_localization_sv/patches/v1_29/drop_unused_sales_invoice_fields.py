"""
Patch v1_29 — Limpieza de campos custom no utilizados en Sales Invoice.

Elimina 15 campos ocultos que nadie lee (datos duplicados en SV DTE Document,
Section Breaks neutralizados, campos de contingencia de feature incompleta).

Restaura sv_dte_section como Section Break real (header visible de la sección DTE).

Actualiza insert_after de 4 campos cuyos anchors son eliminados.
"""

import frappe


def execute():
    # ── 1. Restaurar sv_dte_section como Section Break real ───────────────────
    if frappe.db.exists("Custom Field", "Sales Invoice-sv_dte_section"):
        frappe.db.set_value(
            "Custom Field",
            "Sales Invoice-sv_dte_section",
            {"fieldtype": "Section Break", "hidden": 0},
        )

    # ── 2. Eliminar 15 campos no utilizados ───────────────────────────────────
    FIELDS_TO_DELETE = [
        "sv_anulacion_section",
        "sv_contingencia_section",
        "sv_dte_status",
        "sv_clasifica_msg",
        "sv_codigo_msg",
        "sv_dte_last_payload",
        "sv_dte_last_response",
        "sv_anulacion_tipo",
        "sv_motivo_anulacion",
        "sv_anulacion_sello",
        "sv_anulacion_fecha",
        "sv_anulacion_codigo_generacion_reemplazo",
        "sv_contingencia_event_uuid",
        "sv_contingencia_tipo",
        "sv_contingencia_sello",
    ]
    for fieldname in FIELDS_TO_DELETE:
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True)

    # ── 3. Actualizar insert_after de 4 campos con anchor eliminado ───────────
    REANCHOR = {
        "sv_estado_mh":        "sv_dte_control_number",
        "sv_sello_recepcion":  "sv_estado_mh",
        "sv_observaciones_mh": "sv_fecha_procesamiento",
        "sv_anulacion_status": "sv_total_iva",
    }
    for fieldname, new_anchor in REANCHOR.items():
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, "insert_after", new_anchor)

    frappe.clear_cache()
