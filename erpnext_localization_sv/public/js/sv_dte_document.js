/**
 * SV DTE Document — form script.
 * Botones: Ver en Hacienda, Consultar Estado MH, Invalidar DTE, Abrir Documento Origen.
 */

frappe.ui.form.on("SV DTE Document", {
	refresh(frm) {
		_sv_dte_doc_buttons(frm);
	},
});

function _sv_dte_doc_buttons(frm) {
	const G          = "Acciones DTE";
	const gen_code   = frm.doc.generation_code;
	const mh_status  = frm.doc.mh_status;
	const invalidado = frm.doc.is_invalidated;
	const qr_url     = (frm.doc.mh_verification_url || "").trim();

	// ── Abrir Documento Origen ─────────────────────────────────────────────
	if (frm.doc.source_doctype && frm.doc.source_docname) {
		frm.add_custom_button(__("Abrir Documento Origen"), () => {
			frappe.set_route("Form", frm.doc.source_doctype, frm.doc.source_docname);
		}, G);
	}

	// ── Ver en Hacienda ────────────────────────────────────────────────────
	// El portal (admin.factura.gob.sv/consultaPublica) es una SPA Angular
	// que no acepta params en URL — se muestra diálogo con datos para pegar.
	if (gen_code) {
		const portal_url = qr_url || "https://admin.factura.gob.sv/consultaPublica";

		frm.add_custom_button(__("Ver en Hacienda"), () => {
			const uuid = gen_code;
			// issued_at tiene formato "YYYY-MM-DD HH:MM:SS" — extraer solo fecha
			const raw_date = (frm.doc.issued_at || "").split(" ")[0];
			let fecha_portal = raw_date;
			if (raw_date && raw_date.includes("-")) {
				const [y, m, d] = raw_date.split("-");
				fecha_portal = `${d}/${m}/${y}`;
			}

			// Copiar UUID al portapapeles (best-effort)
			if (navigator.clipboard && navigator.clipboard.writeText) {
				navigator.clipboard.writeText(uuid).catch(() => {});
			}

			const dlg = new frappe.ui.Dialog({
				title: __("Verificar DTE en portal Ministerio de Hacienda"),
				fields: [{
					fieldtype: "HTML",
					options: `
						<p style="margin-bottom:12px;">
							Ingresa estos datos en el portal
							<strong>admin.factura.gob.sv/consultaPublica</strong>:
						</p>
						<table style="width:100%;font-size:13px;border-collapse:collapse;">
							<tr>
								<td style="padding:6px 10px 6px 0;font-weight:bold;white-space:nowrap;vertical-align:top;">
									Fecha de Generación:
								</td>
								<td>
									<code style="background:#f0f4ff;border:1px solid #c7d2fe;padding:4px 10px;border-radius:4px;font-size:13px;display:inline-block;">
										${fecha_portal}
									</code>
								</td>
							</tr>
							<tr>
								<td style="padding:6px 10px 6px 0;font-weight:bold;white-space:nowrap;vertical-align:top;">
									Código de Generación:
								</td>
								<td>
									<code style="background:#f0f4ff;border:1px solid #c7d2fe;padding:4px 10px;border-radius:4px;font-size:12px;word-break:break-all;display:inline-block;">
										${uuid}
									</code>
								</td>
							</tr>
						</table>
						<p style="margin-top:10px;color:#4b5563;font-size:11px;">
							&#x2713; Código de Generación copiado al portapapeles — solo pégalo en el portal.
						</p>
					`,
				}],
				primary_action_label: __("Abrir portal MH"),
				primary_action() {
					window.open(portal_url, "_blank", "noopener,noreferrer");
					dlg.hide();
				},
			});
			dlg.show();
		}, G);
	}

	// ── Consultar Estado MH ────────────────────────────────────────────────
	if (gen_code && mh_status !== "INVALIDADO") {
		frm.add_custom_button(__("Consultar Estado MH"), () => {
			frappe.call({
				method: "erpnext_localization_sv.api.sv_dte_document.refresh_dte_status",
				args: { dte_doc_name: frm.docname },
				freeze: true,
				freeze_message: __("Consultando MH..."),
				callback(r) {
					frm.reload_doc();
					if (r && r.message) {
						const msg    = r.message;
						const estado = msg.estado || msg.clasificaMsg || __("consultado");
						const desc   = msg.descripcionMsg || "";
						const color  = estado === "PROCESADO" ? "green" : "orange";
						const detail = desc
							? `<br><span style="font-size:11px;color:#555;">${desc}</span>`
							: "";
						frappe.msgprint({
							title: __("Estado DTE en Hacienda"),
							indicator: color,
							message: `<b>${estado}</b>${detail}`,
						});
					}
				},
			});
		}, G);
	}

	// ── Invalidar DTE ──────────────────────────────────────────────────────
	// Solo si PROCESADO, no invalidado y fuente es Sales Invoice
	if (
		mh_status === "PROCESADO"
		&& !invalidado
		&& frm.doc.source_doctype === "Sales Invoice"
		&& frm.doc.source_docname
	) {
		frm.add_custom_button(__("Invalidar DTE"), () => {
			frappe.prompt(
				[
					{
						label: __("Tipo de Invalidación"),
						fieldname: "tipo_anulacion",
						fieldtype: "Select",
						options: "1 — Error, reemplazar\n2 — Sin reemplazo\n3 — Devolución",
						reqd: 1,
					},
					{
						label: __("Motivo"),
						fieldname: "motivo_anulacion",
						fieldtype: "Small Text",
						reqd: 1,
					},
					{
						label: __("UUID Reemplazo (solo tipo 1 ó 3)"),
						fieldname: "codigo_generacion_reemplazo",
						fieldtype: "Data",
						reqd: 0,
					},
				],
				(values) => {
					frappe.call({
						method: "erpnext_localization_sv.api.anulacion.anular_dte",
						args: {
							docname: frm.doc.source_docname,
							tipo_anulacion: parseInt(values.tipo_anulacion.split(" ")[0]),
							motivo_anulacion: values.motivo_anulacion,
							codigo_generacion_reemplazo: values.codigo_generacion_reemplazo || "",
						},
						freeze: true,
						freeze_message: __("Invalidando DTE..."),
						callback(r) {
							frm.reload_doc();
							frappe.show_alert({ message: __("DTE invalidado"), indicator: "blue" });
						},
					});
				},
				__("Invalidar DTE"),
				__("Confirmar Invalidación")
			);
		}, G).addClass("btn-danger");
	}
}
