"""
Patch v1.9 — Elimina el campo legacy sv_dte_uuid de Sales Invoice.

El campo sv_dte_uuid almacenaba el mismo valor que sv_dte_generation_code
(codigoGeneracion del MH). Era redundante y causaba confusión en la UI
mostrando dos campos idénticos. La fuente canónica es sv_dte_generation_code.

Cambios:
  1. Elimina el Custom Field sv_dte_uuid de Sales Invoice.
  2. Limpia la columna sv_dte_uuid de tabSales Invoice (datos históricos).

Idempotente: puede ejecutarse múltiples veces sin efecto colateral.
"""

import frappe


def execute():
    # 1. Eliminar el Custom Field si existe
    if frappe.db.exists("Custom Field", "Sales Invoice-sv_dte_uuid"):
        frappe.delete_doc("Custom Field", "Sales Invoice-sv_dte_uuid", ignore_permissions=True)

    # 2. Limpiar la columna en tabSales Invoice (MariaDB conserva la columna hasta
    #    que se ejecute un ALTER TABLE, que Frappe hace en el siguiente migrate)
    #    Setear a NULL para que no queden datos huérfanos.
    frappe.db.sql(
        "UPDATE `tabSales Invoice` SET sv_dte_uuid = NULL WHERE sv_dte_uuid IS NOT NULL"
    )

    frappe.db.commit()
