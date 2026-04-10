frappe.ui.form.on("Address", {
    refresh(frm) {
        frm.set_query("sv_municipio", function () {
            return {
                filters: frm.doc.sv_departamento
                    ? { departamento: frm.doc.sv_departamento }
                    : {},
            };
        });

        frm.set_query("sv_distrito", function () {
            return {
                filters: frm.doc.sv_municipio
                    ? { municipio: frm.doc.sv_municipio }
                    : {},
            };
        });
    },

    sv_departamento(frm) {
        frm.set_value("sv_municipio", "");
        frm.set_value("sv_distrito", "");
    },

    sv_municipio(frm) {
        frm.set_value("sv_distrito", "");
    },
});
