"""
Patch v1.22 — Simplifica la sección DTE en Sales Invoice.

Elimina las secciones DTE / Invalidación / Contingencia como secciones
colapsables separadas e integra los 5 campos más relevantes de forma
inline en el formulario estándar, justo después de due_date.

Campos visibles tras el patch (orden en el form):
  due_date
    → sv_dte_document_type   — Tipo DTE (editable antes de emitir)
    → sv_dte_generation_code — Código de Generación (read_only)
    → sv_dte_control_number  — Número de Control (read_only)
    → sv_estado_mh           — Estado MH (read_only)
    → sv_anulacion_status    — Estado Invalidación (read_only)

Todo lo demás queda hidden=1 (los datos se conservan en DB y
son accesibles desde SV DTE Document).
"""


def execute() -> None:
    import frappe

    # ── 1. Reposicionar y mantener visibles los campos clave ──────────────────
    visible_chain = [
        ("sv_dte_document_type",  "due_date"),
        ("sv_dte_generation_code", "sv_dte_document_type"),
        ("sv_dte_control_number",  "sv_dte_generation_code"),
        ("sv_estado_mh",           "sv_dte_control_number"),
        ("sv_anulacion_status",    "sv_estado_mh"),
    ]
    for fieldname, insert_after in visible_chain:
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, {
                "insert_after": insert_after,
                "hidden": 0,
            })

    # ── 2. Ocultar todo lo demás (datos se conservan) ─────────────────────────
    hide_fields = [
        # Secciones
        "sv_dte_section",
        "sv_anulacion_section",
        "sv_contingencia_section",
        # Campos redundantes o movidos a SV DTE Document
        "sv_dte_environment",
        "sv_dte_status",
        "sv_clasifica_msg",
        "sv_codigo_msg",
        "sv_sello_recepcion",
        "sv_dte_sent_at",
        "sv_fecha_procesamiento",
        "sv_dte_last_payload",
        "sv_dte_last_response",
        "sv_observaciones_mh",
        "sv_dte_qr_url",
        "sv_total_iva",
        # Invalidación — detalle en SV DTE Document
        "sv_anulacion_tipo",
        "sv_motivo_anulacion",
        "sv_anulacion_sello",
        "sv_anulacion_fecha",
        "sv_anulacion_codigo_generacion_reemplazo",
        # Contingencia
        "sv_contingencia_event_uuid",
        "sv_contingencia_tipo",
        "sv_contingencia_sello",
    ]
    for fieldname in hide_fields:
        cf_name = f"Sales Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, "hidden", 1)

    frappe.db.commit()
    frappe.logger().info(
        "[v1_22] Sales Invoice DTE simplificado — 5 campos inline, secciones ocultas."
    )
