import frappe
from frappe.model.document import Document


class SVDistrito(Document):
    def autoname(self):
        self.name = f"{self.municipio}-{self.nombre}"
