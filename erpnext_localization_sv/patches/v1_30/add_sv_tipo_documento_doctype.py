"""
Patch v1.30 — Crea doctype SV Tipo Documento (CAT-22) y carga sus 5 registros.

CAT-22 = catálogo de tipos de documento de identificación personal del MH:
  36 = NIT, 13 = DUI, 02 = Carnet Residente, 03 = Pasaporte, 37 = Otro

El doctype se instala automáticamente por bench migrate (JSON en doctype/).
Este patch carga el fixture con los registros.
"""


def execute() -> None:
    from frappe.utils.fixtures import sync_fixtures

    sync_fixtures(app="erpnext_localization_sv")
