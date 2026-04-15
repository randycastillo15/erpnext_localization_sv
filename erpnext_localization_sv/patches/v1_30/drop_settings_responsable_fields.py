"""
Patch v1.30 — Elimina campos Responsable de SV DTE Settings y migra al usuario admin.

Acciones:
1. Elimina los 4 DocFields de SV DTE Settings:
   responsable_section, sv_nombre_responsable, sv_tipo_doc_responsable, sv_num_doc_responsable

2. Asigna al usuario Administrator los datos que tenía SV DTE Settings,
   para que las invalidaciones/contingencias sigan funcionando sin reconfiguración.

3. Asigna el rol 'DTE Responsable' al usuario Administrator.
"""


def execute() -> None:
    import frappe

    # 1. Leer datos actuales desde tabSingles directamente (sin validación de esquema).
    #    get_single_value falla si el campo ya no existe en el DocType JSON.
    #    get_value en la tabla "Singles" falla porque esa tabla no tiene columna 'modified'.
    def _read_single(field: str) -> str:
        rows = frappe.db.sql(
            "SELECT `value` FROM `tabSingles` WHERE `doctype`='SV DTE Settings' AND `field`=%s LIMIT 1",
            (field,),
        )
        return rows[0][0] if rows else ""

    tipo_doc = _read_single("sv_tipo_doc_responsable") or "13"
    num_doc = _read_single("sv_num_doc_responsable") or ""

    # 2. Eliminar DocFields nativos de SV DTE Settings
    fields_to_drop = [
        "responsable_section",
        "sv_nombre_responsable",
        "sv_tipo_doc_responsable",
        "sv_num_doc_responsable",
    ]
    for fname in fields_to_drop:
        frappe.db.delete("DocField", {
            "parent": "SV DTE Settings",
            "fieldname": fname,
        })
        # Eliminar también el valor almacenado en SingleValue
        frappe.db.delete("Singles", {
            "doctype": "SV DTE Settings",
            "field": fname,
        })

    # 3. Poblar el usuario Administrator con los datos migrados
    if num_doc and frappe.db.exists("User", "Administrator"):
        frappe.db.set_value("User", "Administrator", {
            "sv_tipo_doc_responsable": tipo_doc,
            "sv_num_doc_responsable": num_doc,
        }, update_modified=False)

    # 4. Asignar rol DTE Responsable al usuario Administrator
    admin_roles = frappe.get_all(
        "Has Role",
        filters={"parent": "Administrator", "role": "DTE Responsable"},
        limit=1,
    )
    if not admin_roles:
        user_doc = frappe.get_doc("User", "Administrator")
        user_doc.append("roles", {"role": "DTE Responsable"})
        user_doc.save(ignore_permissions=True)

    frappe.db.commit()
