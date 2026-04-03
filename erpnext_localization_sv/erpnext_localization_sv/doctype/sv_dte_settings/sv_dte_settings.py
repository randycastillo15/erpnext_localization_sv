import frappe
from frappe.model.document import Document


class SVDTESettings(Document):
    def validate(self):
        if self.nit_emisor and len(self.nit_emisor.replace("-", "")) != 14:
            frappe.throw("NIT Emisor debe tener 14 dígitos (sin guiones)")
