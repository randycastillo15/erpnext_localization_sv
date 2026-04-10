"""
Patch v1.15 — Elimina campos legacy de dirección/contacto de Customer.

Pasos:
  1. Migración final: crea Address para cualquier Customer que aún tenga datos
     en campos legacy pero no tenga un Address con sv_departamento.
  2. Elimina los Custom Field docs (metadatos de Frappe).
  3. Elimina las columnas físicas de tabCustomer (limpieza real de DB).
"""

_LEGACY_FIELDS = [
    "sv_col_break_dir",
    "sv_direccion_departamento",
    "sv_direccion_municipio",
    "sv_direccion_complemento",
    "sv_correo",
    "sv_telefono",
]


def execute() -> None:
    import frappe

    # ── 1. Migración final ─────────────────────────────────────────────────
    _migrate_remaining(frappe)

    # ── 2. Eliminar Custom Field docs ──────────────────────────────────────
    for fieldname in _LEGACY_FIELDS:
        cf_name = f"Customer-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True)

    frappe.db.commit()

    # ── 3. Eliminar columnas físicas de tabCustomer ────────────────────────
    # Solo las columnas de datos (no sv_col_break_dir que no tiene columna)
    _db_columns = [
        "sv_direccion_departamento",
        "sv_direccion_municipio",
        "sv_direccion_complemento",
        "sv_correo",
        "sv_telefono",
    ]
    for col in _db_columns:
        if frappe.db.has_column("Customer", col):
            frappe.db.sql(f"ALTER TABLE `tabCustomer` DROP COLUMN `{col}`")

    frappe.db.commit()
    frappe.logger().info("[v1_15] Campos legacy eliminados de Customer.")


def _migrate_remaining(frappe) -> None:
    """Crea Address para Customers que aún tienen datos legacy sin Address DTE."""
    customers = frappe.db.sql(
        """
        SELECT name, customer_name,
               sv_direccion_departamento, sv_direccion_municipio,
               sv_direccion_complemento, sv_correo, sv_telefono
        FROM `tabCustomer`
        WHERE COALESCE(sv_direccion_departamento, '') != ''
        """,
        as_dict=True,
    )

    migrated = 0
    for c in customers:
        # Verificar si ya tiene un Address con sv_departamento
        existing = frappe.db.get_all(
            "Dynamic Link",
            filters={"link_doctype": "Customer", "link_name": c.name, "parenttype": "Address"},
            fields=["parent"],
        )
        if any(frappe.db.get_value("Address", lnk.parent, "sv_departamento") for lnk in existing):
            continue

        try:
            addr = frappe.new_doc("Address")
            addr.address_title = c.customer_name
            addr.address_type  = "Billing"
            addr.address_line1 = c.sv_direccion_complemento or "—"
            addr.city          = "—"
            addr.country       = "El Salvador"
            addr.email_id      = c.sv_correo or ""
            addr.phone         = c.sv_telefono or ""
            addr.sv_departamento = c.sv_direccion_departamento or ""
            addr.sv_municipio    = c.sv_direccion_municipio or ""
            addr.append("links", {"link_doctype": "Customer", "link_name": c.name})
            addr.insert(ignore_permissions=True)
            migrated += 1
        except Exception as exc:
            frappe.logger().warning(
                "[v1_15] No se pudo migrar Address para '%s': %s", c.name, exc
            )

    if migrated:
        frappe.db.commit()
        frappe.logger().info("[v1_15] Migración final: %d Address creados.", migrated)
