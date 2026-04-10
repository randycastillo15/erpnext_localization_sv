"""
Patch v1.11 — Migra datos de dirección/contacto del receptor de Customer → Address.

Cambios de modelo:
  - Address recibe campos custom: sv_departamento (Link) y sv_municipio (Link)
  - Customer oculta campos legacy: sv_direccion_*, sv_correo, sv_telefono

Migración de datos:
  Para cada Customer con sv_direccion_departamento configurado, crea un Address
  de tipo Billing con los datos DTE si el Customer no tiene ya un Address linked.
  Los campos legacy quedan hidden=1 pero con datos en DB como fallback.
"""


def execute() -> None:
    import frappe
    from erpnext_localization_sv.custom_fields.address import create_address_dte_fields
    from erpnext_localization_sv.custom_fields.customer import create_customer_dte_fields

    # 1. Crear custom fields en Address (inline, sin sección separada)
    create_address_dte_fields()

    # Eliminar sección separada si quedó de una ejecución anterior
    if frappe.db.exists("Custom Field", "Address-sv_dte_section"):
        frappe.delete_doc("Custom Field", "Address-sv_dte_section", ignore_permissions=True)

    # 2. Ocultar campos legacy en Customer (actualiza las Custom Field definitions)
    create_customer_dte_fields()

    legacy_fields = [
        "Customer-sv_direccion_departamento",
        "Customer-sv_direccion_municipio",
        "Customer-sv_direccion_complemento",
        "Customer-sv_correo",
        "Customer-sv_telefono",
        "Customer-sv_col_break_dir",
    ]
    for cf_name in legacy_fields:
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, "hidden", 1)

    frappe.db.commit()

    # 3. Migrar datos a Address para Customers que tienen sv_direccion_departamento
    #    y no tienen aún un Address linked con sv_departamento configurado.
    customers_with_data = frappe.db.get_all(
        "Customer",
        filters={"sv_direccion_departamento": ["!=", ""]},
        fields=["name", "customer_name",
                "sv_direccion_departamento", "sv_direccion_municipio",
                "sv_direccion_complemento", "sv_correo", "sv_telefono"],
    )

    migrated = 0
    for c in customers_with_data:
        if not c.sv_direccion_departamento:
            continue

        # Verificar si ya existe un Address con sv_departamento para este Customer
        existing = frappe.db.get_all(
            "Dynamic Link",
            filters={"link_doctype": "Customer", "link_name": c.name, "parenttype": "Address"},
            fields=["parent"],
        )
        already_migrated = False
        for lnk in existing:
            if frappe.db.get_value("Address", lnk.parent, "sv_departamento"):
                already_migrated = True
                break

        if already_migrated:
            continue

        # Crear nuevo Address con los datos DTE
        try:
            addr = frappe.new_doc("Address")
            addr.address_title = c.customer_name
            addr.address_type  = "Billing"
            addr.address_line1 = c.sv_direccion_complemento or "—"
            addr.city          = "—"  # campo oculto por v1_13, valor mínimo para compatibilidad
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
                "[v1_11] No se pudo migrar Address para Customer '%s': %s", c.name, exc
            )

    frappe.db.commit()
    frappe.logger().info(
        "[v1_11] Migración completa. Addresses creados: %d / %d customers con datos.",
        migrated, len(customers_with_data),
    )
