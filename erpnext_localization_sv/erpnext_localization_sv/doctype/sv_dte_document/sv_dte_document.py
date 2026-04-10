"""Controller para SV DTE Document — índice operativo de DTEs emitidos."""
from frappe.model.document import Document


class SVDTEDocument(Document):
    @staticmethod
    def get_list_indicator(doc):
        """Color del indicador de estado en la vista de lista."""
        color_map = {
            "PROCESADO":    "green",
            "RECHAZADO":    "red",
            "INVALIDADO":   "orange",
            "PENDIENTE":    "grey",
            "CONTINGENCIA": "blue",
        }
        status = doc.get("mh_status") or ""
        return [status, color_map.get(status, "grey")]
