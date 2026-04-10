frappe.ui.form.on("SV DTE Establishment", {
    refresh(frm) {
        // Filtrar municipio según departamento seleccionado
        frm.set_query("municipio", function () {
            return {
                filters: frm.doc.departamento
                    ? { departamento: frm.doc.departamento }
                    : {},
            };
        });
    },

    departamento(frm) {
        // Limpiar municipio al cambiar departamento
        frm.set_value("municipio", "");
    },
});
