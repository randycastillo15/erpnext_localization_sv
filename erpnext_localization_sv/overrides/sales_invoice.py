"""
Override de Sales Invoice — on_submit handler para emisión automática DTE.

Reglas:
  - Solo activa si SV DTE Settings.emitir_al_someter = 1.
  - Solo FE y CCF (tipos soportados con validación completa en MH real).
  - NC, ND, contingencia e invalidación NO se auto-emiten.
  - Idempotente: si sv_dte_generation_code ya existe, no hace nada (silencioso).
  - Nunca bloquea el submit: cualquier excepción es capturada.
  - En éxito: solo logging (sin msgprint — el operador verá el gen_code al recargar).
  - En fallo: frappe.log_error + un msgprint orange no bloqueante.
"""

import frappe

# Tipos de documento para los que se permite auto-emisión.
# Incluye tanto etiquetas ("FE", "CCF") como códigos legacy ("01", "03").
_TIPOS_AUTO_EMIT = frozenset({"FE", "01", "CCF", "03"})


def on_submit(doc, method=None):
    """
    Hook on_submit — no relanza excepciones, no bloquea el submit.
    """
    try:
        settings = frappe.get_single("SV DTE Settings")
    except Exception:
        # SV DTE Settings no existe — continuar sin auto-emisión
        return

    if not settings.get("emitir_al_someter"):
        return

    tipo_doc = doc.get("sv_dte_document_type") or ""
    if tipo_doc not in _TIPOS_AUTO_EMIT:
        return

    if doc.get("sv_dte_generation_code"):
        # Ya emitido — idempotencia, no relanzar ni logear
        return

    try:
        from erpnext_localization_sv.api.dte import emit_dte

        emit_dte(doctype="Sales Invoice", docname=doc.name)
        frappe.logger("dte").info(
            "[on_submit] DTE auto-emitido exitosamente: %s (tipo=%s)", doc.name, tipo_doc
        )
    except Exception as exc:
        frappe.log_error(
            title=f"[DTE] Auto-emit fallido: {doc.name}",
            message=str(exc),
        )
        frappe.msgprint(
            f"El DTE no pudo emitirse automáticamente. "
            f"Use el botón 'Emitir DTE' para reintentar.",
            indicator="orange",
            title="Emisión automática falló",
            raise_exception=False,
        )
