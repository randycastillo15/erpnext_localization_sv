import frappe
from frappe.model.document import Document


class SVMunicipio(Document):
    def autoname(self):
        self.name = f"{self.departamento}-{self.codigo}"
