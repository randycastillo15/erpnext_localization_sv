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
	// mh_verification_url contiene la URL completa: ?ambiente=XX&codGen=UUID&fechaEmi=DATE
	// Siempre usa la fecha de EMISIÓN (posting_date de la factura), nunca la de invalidación.
	if (gen_code) {
		frm.add_custom_button(__("Ver en Hacienda"), () => {
			if (qr_url && qr_url.includes("codGen=")) {
				// URL completa ya disponible — abrir directamente
				window.open(qr_url, "_blank", "noopener,noreferrer");
			} else {
				// Fallback: obtener posting_date de la Sales Invoice de origen
				// (issued_at puede diferir de posting_date — nunca usar fecha de invalidación)
				const _open = (fecha) => {
					const url = `https://admin.factura.gob.sv/consultaPublica?ambiente=00&codGen=${gen_code}&fechaEmi=${fecha}`;
					window.open(url, "_blank", "noopener,noreferrer");
				};
				if (frm.doc.source_doctype === "Sales Invoice" && frm.doc.source_docname) {
					frappe.db.get_value(
						"Sales Invoice", frm.doc.source_docname, "posting_date",
						(r) => _open((r && r.posting_date) || (frm.doc.issued_at || "").split(" ")[0])
					);
				} else {
					_open((frm.doc.issued_at || "").split(" ")[0]);
				}
			}
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
