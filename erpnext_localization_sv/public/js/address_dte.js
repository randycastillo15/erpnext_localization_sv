frappe.ui.form.on("Address", {
    refresh(frm) {
        frm.set_query("sv_municipio", function () {
            return {
                filters: frm.doc.sv_departamento
                    ? { departamento: frm.doc.sv_departamento }
                    : {},
            };
        });
    },

    sv_departamento(frm) {
        frm.set_value("sv_municipio", "");
    },
});
