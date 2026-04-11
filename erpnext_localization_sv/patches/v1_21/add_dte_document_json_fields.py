"""
Patch v1.21 — Agrega campos JSON al SV DTE Document y hace backfill desde SV DTE Log.

Nuevos campos en el DocType (el schema ya está en el JSON):
  - mh_request_json   : Code/JSON — request enviado al gateway (sanitizado)
  - mh_response_json  : Code/JSON — response recibido de MH (sanitizado)
  - observaciones_mh  : Small Text — observaciones MH en texto plano
  - tipo_anulacion    : Data — tipo de invalidación (1/2/3)
  - motivo_anulacion  : Small Text — motivo de la invalidación

Backfill: para cada SV DTE Document existente, busca el SV DTE Log de emisión
más reciente y copia request_json / response_json.
"""


def execute() -> None:
    import frappe

    # Backfill request/response JSON desde SV DTE Log para registros existentes
    dte_docs = frappe.db.get_all(
        "SV DTE Document",
        filters={"generation_code": ["is", "set"]},
        fields=["name", "generation_code", "source_docname"],
    )

    for dtedoc in dte_docs:
        gen_code = dtedoc.get("generation_code") or ""
        source = dtedoc.get("source_docname") or ""
        if not gen_code and not source:
            continue

        # Buscar el log de emisión más reciente para este DTE
        filters = {"tipo_evento": "emision"}
        if gen_code:
            filters["codigo_generacion"] = gen_code
        elif source:
            filters["reference_docname"] = source

        log = frappe.db.get_value(
            "SV DTE Log",
            filters,
            ["request_json", "response_json"],
            as_dict=True,
            order_by="creation desc",
        )

        if not log:
            continue

        update_values = {}
        if log.get("request_json"):
            update_values["mh_request_json"] = log["request_json"]
        if log.get("response_json"):
            update_values["mh_response_json"] = log["response_json"]
            # Extraer observaciones del JSON de respuesta si las hay
            try:
                import json
                resp = json.loads(log["response_json"])
                obs_list = resp.get("observaciones") or []
                if obs_list:
                    update_values["observaciones_mh"] = "\n".join(
                        f"• {o}" for o in obs_list
                    )
            except Exception:
                pass

        if update_values:
            frappe.db.set_value("SV DTE Document", dtedoc["name"], update_values)

    frappe.db.commit()
    frappe.logger().info(
        "[v1_21] SV DTE Document: campos JSON agregados y backfill desde SV DTE Log completado."
    )
