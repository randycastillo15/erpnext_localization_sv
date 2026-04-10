frappe.ui.form.on("Customer", {
    sv_cod_actividad(frm) {
        const codigo = frm.doc.sv_cod_actividad;
        if (!codigo) {
            frm.set_value("sv_desc_actividad", "");
            return;
        }
        frappe.db.get_value("SV Actividad Economica", codigo, "descripcion")
            .then(r => {
                if (r && r.message && r.message.descripcion) {
                    frm.set_value("sv_desc_actividad", r.message.descripcion);
                }
            });
    },
});
