frappe.ui.form.on("Customer", {
    refresh(frm) {
        // Filtrar municipio según departamento seleccionado
        frm.set_query("sv_direccion_municipio", function () {
            return {
                filters: frm.doc.sv_direccion_departamento
                    ? { departamento: frm.doc.sv_direccion_departamento }
                    : {},
            };
        });
    },

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

    sv_direccion_departamento(frm) {
        // Limpiar municipio al cambiar departamento
        frm.set_value("sv_direccion_municipio", "");
    },
});
