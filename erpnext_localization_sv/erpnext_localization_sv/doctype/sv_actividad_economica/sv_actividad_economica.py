import frappe
from frappe.model.document import Document


class SVActividadEconomica(Document):
    def before_save(self):
        desc = (self.descripcion or "")[:120]
        self.titulo = f"{self.codigo} — {desc}"
