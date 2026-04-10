frappe.ui.form.on("SV DTE Settings", {
    cod_actividad(frm) {
        const codigo = frm.doc.cod_actividad;
        if (!codigo) {
            frm.set_value("desc_actividad", "");
            return;
        }
        frappe.db.get_value("SV Actividad Economica", codigo, "descripcion")
            .then(r => {
                if (r && r.message && r.message.descripcion) {
                    frm.set_value("desc_actividad", r.message.descripcion);
                }
            });
    },
});
