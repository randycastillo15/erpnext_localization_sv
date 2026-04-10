"""
Patch v1.10 — Agrega campo titulo a los DocTypes catálogo y lo popula.

show_title_field_in_link=1 permite que los campos Link muestren
"código — descripción" en lugar de solo el código (name).
"""


def execute() -> None:
    import frappe
    from frappe.utils.fixtures import sync_fixtures

    # Recargar fixtures con el campo titulo incluido
    sync_fixtures(app="erpnext_localization_sv")

    # Poblar titulo en registros existentes que no lo tengan aún
    # (por si sync_fixtures no ejecuta before_save)
    for rec in frappe.db.get_all("SV Departamento", fields=["name", "codigo", "nombre"]):
        frappe.db.set_value(
            "SV Departamento", rec.name, "titulo",
            f"{rec.codigo} — {rec.nombre or ''}",
            update_modified=False,
        )

    for rec in frappe.db.get_all("SV Municipio", fields=["name", "codigo", "nombre"]):
        frappe.db.set_value(
            "SV Municipio", rec.name, "titulo",
            f"{rec.codigo} — {rec.nombre or ''}",
            update_modified=False,
        )

    for rec in frappe.db.get_all("SV Actividad Economica", fields=["name", "codigo", "descripcion"]):
        desc = (rec.descripcion or "")[:120]
        frappe.db.set_value(
            "SV Actividad Economica", rec.name, "titulo",
            f"{rec.codigo} — {desc}",
            update_modified=False,
        )

    frappe.db.commit()
