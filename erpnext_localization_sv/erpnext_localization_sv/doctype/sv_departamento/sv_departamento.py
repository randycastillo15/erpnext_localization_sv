import frappe
from frappe.model.document import Document


class SVDepartamento(Document):
    def before_save(self):
        self.titulo = f"{self.codigo} — {self.nombre or ''}"
