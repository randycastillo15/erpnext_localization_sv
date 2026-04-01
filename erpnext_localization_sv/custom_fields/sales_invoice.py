"""
Custom Fields DTE para Sales Invoice.

Definición centralizada usada desde:
  - patches/v1_0/install.py       (after_install — sitios nuevos)
  - patches/v1_0/add_dte_custom_fields.py  (patch versionado — sitios existentes)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# insert_after encadena los campos explícitamente dentro de la sección.
# El section break se ancla a "discount_amount", último campo de "Additional Discount".
# Esto coloca la sección DTE justo debajo del bloque de descuentos, antes de Totales.
_DTE_FIELDS = {
	"Sales Invoice": [
		{
			"fieldname": "sv_dte_section",
			"fieldtype": "Section Break",
			"label": "DTE El Salvador",
			"collapsible": 1,
			"insert_after": "discount_amount",
		},
		{
			"fieldname": "sv_dte_status",
			"fieldtype": "Data",
			"label": "DTE Status",
			"read_only": 1,
			"no_copy": 1,
			"insert_after": "sv_dte_section",
		},
		{
			"fieldname": "sv_dte_uuid",
			"fieldtype": "Data",
			"label": "DTE UUID",
			"read_only": 1,
			"no_copy": 1,
			"insert_after": "sv_dte_status",
		},
		{
			"fieldname": "sv_dte_sent_at",
			"fieldtype": "Datetime",
			"label": "DTE Enviado el",
			"read_only": 1,
			"no_copy": 1,
			"insert_after": "sv_dte_uuid",
		},
		{
			"fieldname": "sv_dte_last_response",
			"fieldtype": "Long Text",
			"label": "DTE Última Respuesta",
			"read_only": 1,
			"no_copy": 1,
			"insert_after": "sv_dte_sent_at",
		},
	]
}


def create_dte_custom_fields() -> None:
	"""
	Crea o actualiza los Custom Fields DTE en Sales Invoice.
	Idempotente: si los campos ya existen, los actualiza sin duplicar.
	"""
	create_custom_fields(_DTE_FIELDS, ignore_validate=True)
	frappe.logger().info(
		"[erpnext_localization_sv] Custom Fields DTE en Sales Invoice creados/actualizados"
	)
