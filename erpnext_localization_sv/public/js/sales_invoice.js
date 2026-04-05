/**
 * DTE El Salvador — botones de acción en Sales Invoice.
 * Sprint 5: Emitir, Consultar Estado, Re-emitir, Anular DTE.
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

	// Anular DTE — solo si PROCESADO y sin anulación previa
	if (estado_mh === "PROCESADO" && !anulado) {
		frm.add_custom_button(__("Anular DTE"), () => {
			frappe.prompt(
				[
					{
						label: __("Tipo de Anulación"),
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
						freeze_message: __("Anulando DTE..."),
						callback(r) {
							frm.reload_doc();
							frappe.show_alert({ message: __("DTE invalidado"), indicator: "blue" });
						},
					});
				},
				__("Anular DTE"),
				__("Confirmar Anulación")
			);
		}, G).addClass("btn-danger");
	}
}
