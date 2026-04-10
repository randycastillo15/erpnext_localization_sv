"""
Patch v1.9 — Rellena SV DTE Document con todos los DTEs emitidos.

Crea un SV DTE Document por cada Sales Invoice que tenga
sv_dte_generation_code poblado. Idempotente: sync_on_emit hace
lookup por generation_code antes de insert, por lo que no crea duplicados.

Ejecutar después de bench migrate (el DocType ya existe en DB).
"""
import frappe

_TIPO_CODE_MAP = {"FE": "01", "CCF": "03", "NC": "05", "ND": "06"}


def execute():
    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters={"sv_dte_generation_code": ["not in", ["", None]]},
        fields=[
            "name",
            "company",
            "customer",
            "customer_name",
            "sv_dte_generation_code",
            "sv_dte_control_number",
            "sv_estado_mh",
            "sv_dte_document_type",
            "sv_sello_recepcion",
            "sv_fecha_procesamiento",
            "sv_dte_qr_url",
            "sv_anulacion_status",
            "sv_anulacion_fecha",
            "sv_anulacion_codigo_generacion_reemplazo",
            "sv_dte_sent_at",
        ],
    )

    from erpnext_localization_sv.api.dte_document_sync import (
        sync_on_emit,
        sync_on_invalidation,
    )

    ambiente = frappe.db.get_single_value("SV DTE Settings", "ambiente") or "00"

    for inv in invoices:
        gen_code = inv.get("sv_dte_generation_code")
        if not gen_code:
            continue

        dte_type_label = inv.get("sv_dte_document_type") or "FE"
        dte_type_code = _TIPO_CODE_MAP.get(dte_type_label, "01")

        try:
            sync_on_emit(
                source_doctype="Sales Invoice",
                source_docname=inv["name"],
                generation_code=gen_code,
                control_number=inv.get("sv_dte_control_number"),
                mh_status=inv.get("sv_estado_mh"),
                dte_type_label=dte_type_label,
                dte_type_code=dte_type_code,
                reception_seal=inv.get("sv_sello_recepcion"),
                mh_processed_at=inv.get("sv_fecha_procesamiento"),
                ambiente=ambiente,
                company=inv.get("company"),
                customer=inv.get("customer"),
                customer_name=inv.get("customer_name"),
                mh_verification_url=inv.get("sv_dte_qr_url"),
            )
        except Exception as exc:
            frappe.logger().warning(
                "backfill_dte_documents: error en %s: %s", inv["name"], exc
            )
            continue

        # Si fue invalidado, persistir también la invalidación
        if inv.get("sv_anulacion_status") == "Invalidado":
            try:
                sync_on_invalidation(
                    generation_code=gen_code,
                    invalidated_at=inv.get("sv_anulacion_fecha"),
                    replacement_generation_code=inv.get(
                        "sv_anulacion_codigo_generacion_reemplazo"
                    ),
                )
            except Exception as exc:
                frappe.logger().warning(
                    "backfill_dte_documents: error en invalidación %s: %s",
                    inv["name"],
                    exc,
                )

    frappe.db.commit()
