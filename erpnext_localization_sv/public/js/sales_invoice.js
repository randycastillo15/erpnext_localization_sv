/**
 * DTE El Salvador — botones de acción en Sales Invoice.
 * Sprint 5: Emitir, Consultar Estado, Re-emitir, Anular DTE.
 * Sprint 6: Terminología → Invalidar DTE. Botón Ver en Hacienda.
 * Sprint 7: Ver en Hacienda muestra diálogo con fecha/UUID listos + copia UUID al portapapeles.
 * Sprint 9: Visibilidad de botones controlada por roles DTE.
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

	// Verificación de roles DTE (client-side — el servidor también valida)
	const roles       = frappe.user_roles || [];
	const canEmit     = roles.some(r => ["DTE Operador", "DTE Responsable", "DTE Admin"].includes(r));
	const canInvalidar = roles.includes("DTE Responsable");
	const canRead     = roles.some(r => ["DTE Operador", "DTE Responsable", "DTE Admin", "DTE Auditor"].includes(r));

	// Ver Detalle DTE — navega al SV DTE Document asociado
	if (gen_code && canRead) {
		frm.add_custom_button(__("Ver Detalle DTE"), () => {
			frappe.db.get_value(
				"SV DTE Document",
				{ generation_code: gen_code },
				"name",
				(r) => {
					if (r && r.name) {
						frappe.set_route("Form", "SV DTE Document", r.name);
					} else {
						frappe.msgprint({
							title: __("Documento DTE no encontrado"),
							message: __("No se encontró el registro SV DTE Document para este código de generación."),
							indicator: "orange",
						});
					}
				}
			);
		}, G);
	}

	// Emitir DTE — solo si tipo_doc seleccionado y aún sin gen_code
	if (tipo_doc && !gen_code && canEmit) {
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

	// Ver en Hacienda — abre directamente el portal MH con los parámetros correctos.
	// sv_dte_qr_url contiene la URL completa: ?ambiente=XX&codGen=UUID&fechaEmi=YYYY-MM-DD
	// Fallback para facturas legacy (emitidas antes del patch): construir URL desde componentes.
	if (gen_code && canRead) {
		frm.add_custom_button(__("Ver en Hacienda"), () => {
			let url = qr_url;
			if (!url || !url.includes("codGen=")) {
				const ambiente = frm.doc.sv_dte_environment || "00";
				const fecha    = frm.doc.posting_date || "";
				url = `https://admin.factura.gob.sv/consultaPublica?ambiente=${ambiente}&codGen=${gen_code}&fechaEmi=${fecha}`;
			}
			window.open(url, "_blank", "noopener,noreferrer");
		}, G);
	}

	// Consultar Estado MH — si tiene gen_code y no está INVALIDADO
	if (gen_code && estado_mh !== "INVALIDADO" && canRead) {
		frm.add_custom_button(__("Consultar Estado MH"), () => {
			frappe.call({
				method: "erpnext_localization_sv.api.dte.get_dte_status",
				args: { docname: frm.docname },
				freeze: true,
				freeze_message: __("Consultando MH..."),
				callback(r) {
					frm.reload_doc();
					if (r && r.message) {
						const msg = r.message;
						const estado = msg.estado || msg.clasificaMsg || __("consultado");
						const desc   = msg.descripcionMsg || msg.observaciones || "";
						const color  = estado === "PROCESADO" ? "green" : "orange";
						const detail = desc ? `<br><span style="font-size:11px;color:#555;">${desc}</span>` : "";
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

	// Re-emitir DTE — solo si el último estado es RECHAZADO
	if (gen_code && estado_mh === "RECHAZADO" && canEmit) {
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
	if (estado_mh === "PROCESADO" && !anulado && canInvalidar) {
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
