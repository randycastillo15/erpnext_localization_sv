/**
 * DTE El Salvador — botones de acción en Sales Invoice.
 * Sprint 5: Emitir, Consultar Estado, Re-emitir, Anular DTE.
 * Sprint 6: Terminología → Invalidar DTE. Botón Ver en Hacienda.
 * Sprint 7: Ver en Hacienda muestra diálogo con fecha/UUID listos + copia UUID al portapapeles.
 */

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		_dte_sv_refresh_buttons(frm);
	},
});

function _dte_sv_refresh_buttons(frm) {
	if (frm.doc.docstatus !== 1) return;

	const gen_code  = frm.doc.sv_dte_generation_code;
	const estado_mh = frm.doc.sv_estado_mh;
	const anulado   = frm.doc.sv_anulacion_status;
	const tipo_doc  = frm.doc.sv_dte_document_type;
	const qr_url    = (frm.doc.sv_dte_qr_url || "").trim();
	const G = "DTE El Salvador";

	// Emitir DTE — solo si tipo_doc seleccionado y aún sin gen_code
	if (tipo_doc && !gen_code) {
		frm.add_custom_button(__("Emitir DTE"), () => {
			frappe.call({
				method: "erpnext_localization_sv.api.dte.emit_dte",
				args: { doctype: frm.doctype, docname: frm.docname },
				freeze: true,
				freeze_message: __("Emitiendo DTE..."),
				callback(r) {
					frm.reload_doc();
					frappe.show_alert({ message: __("DTE emitido"), indicator: "green" });
				},
			});
		}, G);
	}

	// Ver en Hacienda — muestra diálogo con datos listos para pegar en el portal MH
	// El portal (admin.factura.gob.sv/consultaPublica) es una SPA Angular que no acepta
	// params en la URL. Se copia el UUID al portapapeles y se muestra la fecha formateada.
	if (qr_url && gen_code) {
		frm.add_custom_button(__("Ver en Hacienda"), () => {
			const uuid = gen_code;
			const raw_date = frm.doc.posting_date || "";
			// El portal espera fecha en formato DD/MM/YYYY
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
					window.open(qr_url, "_blank", "noopener,noreferrer");
					dlg.hide();
				},
			});
			dlg.show();
		}, G);
	}

	// Consultar Estado MH — si tiene gen_code y no está INVALIDADO
	if (gen_code && estado_mh !== "INVALIDADO") {
		frm.add_custom_button(__("Consultar Estado MH"), () => {
			frappe.call({
				method: "erpnext_localization_sv.api.dte.get_dte_status",
				args: { docname: frm.docname },
				freeze: true,
				freeze_message: __("Consultando MH..."),
				callback(r) {
					frm.reload_doc();
				},
			});
		}, G);
	}

	// Re-emitir DTE — solo si el último estado es RECHAZADO
	if (gen_code && estado_mh === "RECHAZADO") {
		frm.add_custom_button(__("Re-emitir DTE"), () => {
			frappe.confirm(
				__("El DTE fue rechazado por MH. ¿Desea intentar nuevamente?"),
				() => frappe.call({
					method: "erpnext_localization_sv.api.dte.emit_dte",
					args: { doctype: frm.doctype, docname: frm.docname },
					freeze: true,
					freeze_message: __("Re-emitiendo..."),
					callback(r) {
						frm.reload_doc();
					},
				})
			);
		}, G);
	}

	// Invalidar DTE — solo si PROCESADO y sin invalidación previa
	if (estado_mh === "PROCESADO" && !anulado) {
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
							docname: frm.docname,
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
