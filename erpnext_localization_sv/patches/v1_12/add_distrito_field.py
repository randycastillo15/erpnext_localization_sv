"""
Patch v1.12 — Agrega campo sv_distrito (Link → SV Distrito) al formulario Address,
filtrado por sv_municipio. El DocType SV Distrito y su fixture (262 registros)
se cargan automáticamente vía hooks.fixtures durante bench migrate.
"""


def execute() -> None:
    import frappe
    from erpnext_localization_sv.custom_fields.address import create_address_dte_fields

    create_address_dte_fields()
    frappe.db.commit()

    frappe.logger().info("[v1_12] Campo sv_distrito agregado a Address.")
