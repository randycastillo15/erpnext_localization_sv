/**
 * SV DTE Document — list view settings.
 * Indicador de color por estado MH.
 */

frappe.listview_settings["SV DTE Document"] = {
	add_fields: ["mh_status", "is_invalidated", "dte_type_label"],

	get_indicator(doc) {
		const map = {
			"PROCESADO":    ["green",  "PROCESADO"],
			"RECHAZADO":    ["red",    "RECHAZADO"],
			"INVALIDADO":   ["orange", "INVALIDADO"],
			"PENDIENTE":    ["grey",   "PENDIENTE"],
			"CONTINGENCIA": ["blue",   "CONTINGENCIA"],
		};
		const entry = map[doc.mh_status];
		return entry || ["grey", doc.mh_status || "—"];
	},
};
