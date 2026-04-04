import frappe
from frappe.model.document import Document


class SVDTESettings(Document):
    def validate(self):
        if self.nit_emisor:
            clean = self.nit_emisor.replace("-", "")
            if len(clean) not in (9, 14):
                frappe.throw("NIT Emisor debe tener 9 dígitos (DUI homologado) o 14 dígitos (NIT), sin guiones")
