"""
Patch v1.7 — Actualiza Print Format "DTE El Salvador" con datos fiscales del receptor.

Cambios respecto a v1.6:
  - Para CCF/NC/ND: muestra NIT, NRC, giro y dirección del Customer bajo el nombre.
  - El bloque es completamente defensivo: todas las condiciones se evalúan antes
    de acceder a campos del Customer — no lanza excepción si el campo está vacío.
  - FE sigue mostrando solo el nombre del receptor (Consumidor Final o customer_name).
  - Sin cambios en lógica de negocio, items, totales, MH info ni QR.
  - Idempotente: si el formato existe, actualiza; si no, inserta.
"""

import frappe

_NAME = "DTE El Salvador"

_HTML = """{%- set tipo_map = {
    "FE":  "Factura Electrónica (01)",
    "CCF": "Comprobante de Crédito Fiscal (03)",
    "NC":  "Nota de Crédito (05)",
    "ND":  "Nota de Débito (06)"
} -%}
<style>
  body { font-family: Arial, sans-serif; font-size: 11px; margin: 0; padding: 20px; }
  .dte-header { text-align: center; border-bottom: 2px solid #333;
                padding-bottom: 10px; margin-bottom: 12px; }
  .dte-tipo { font-size: 16px; font-weight: bold; }
  .dte-company { font-size: 10px; color: #555; margin-top: 4px; }
  .label { font-weight: bold; }
  table.meta { width: 100%; margin-bottom: 8px; }
  table.meta td { padding: 2px 6px 2px 0; vertical-align: top; }
  .receptor-block { margin-bottom: 8px; }
  .receptor-nombre { font-weight: bold; }
  .receptor-fiscal { font-size: 10px; color: #444; margin-top: 2px; line-height: 1.5; }
  table.items { width: 100%; border-collapse: collapse; margin-top: 10px; }
  table.items th, table.items td { border: 1px solid #ccc; padding: 4px 6px; }
  table.items th { background: #f0f0f0; text-align: left; }
  .totals { text-align: right; margin-top: 10px; border-top: 1px solid #ccc; padding-top: 6px; }
  .totals div { margin-bottom: 2px; }
  .total-final { font-size: 13px; font-weight: bold; margin-top: 4px; }
  .mh-info { margin-top: 12px; padding: 8px; border: 1px solid #ddd;
             background: #fafafa; font-size: 10px; line-height: 1.6; }
  .qr-section { margin-top: 12px; padding: 8px; border: 1px dashed #aaa;
                font-size: 10px; color: #444; word-break: break-all; }
  .qr-pending { color: #aaa; font-style: italic; margin-top: 4px; }
</style>

<div class="dte-header">
  <div class="dte-tipo">
    {{ tipo_map.get(doc.sv_dte_document_type, doc.sv_dte_document_type or "Documento Tributario Electrónico") }}
  </div>
  <div class="dte-company">{{ doc.company }}</div>
</div>

<table class="meta">
  <tr>
    <td><span class="label">N° Control:</span> {{ doc.sv_dte_control_number or "—" }}</td>
    <td><span class="label">Estado MH:</span> {{ doc.sv_estado_mh or "—" }}</td>
  </tr>
  <tr>
    <td colspan="2" style="word-break:break-all;">
      <span class="label">Código Generación:</span> {{ doc.sv_dte_generation_code or "—" }}
    </td>
  </tr>
  <tr>
    <td><span class="label">Fecha:</span> {{ doc.posting_date }}</td>
    <td><span class="label">Receptor:</span> {{ doc.customer_name }}</td>
  </tr>
</table>

<hr/>

{#
  Bloque receptor fiscal — solo para CCF/NC/ND.
  Defensivo: evalúa doc.customer antes de llamar a frappe.get_doc().
  Evalúa cada campo del Customer antes de renderizarlo.
  No lanza excepción si el Customer no tiene datos fiscales configurados.
#}
{%- if doc.sv_dte_document_type in ("CCF", "NC", "ND") and doc.customer -%}
{%- set _c = frappe.get_doc("Customer", doc.customer) -%}
<div class="receptor-block">
  <span class="label">Datos fiscales receptor:</span>
  <div class="receptor-fiscal">
    {%- if _c.sv_nit -%}
    <div>NIT: {{ _c.sv_nit }}{%- if _c.sv_nrc %} &nbsp;|&nbsp; NRC: {{ _c.sv_nrc }}{%- endif -%}</div>
    {%- endif -%}
    {%- if _c.sv_desc_actividad -%}
    <div>Giro: {{ _c.sv_desc_actividad }}</div>
    {%- endif -%}
    {%- if _c.sv_direccion_complemento -%}
    <div>Dirección: {{ _c.sv_direccion_complemento }}</div>
    {%- endif -%}
  </div>
</div>
{%- endif -%}

<table class="items">
  <thead>
    <tr>
      <th>#</th>
      <th>Descripción</th>
      <th>Cant.</th>
      <th>Precio Unit.</th>
      <th>Total</th>
    </tr>
  </thead>
  <tbody>
    {% for item in doc.items %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ item.item_name }}</td>
      <td>{{ item.qty }}</td>
      <td>{{ frappe.utils.fmt_money(item.rate, currency=doc.currency) }}</td>
      <td>{{ frappe.utils.fmt_money(item.amount, currency=doc.currency) }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<div class="totals">
  <div><span class="label">Subtotal:</span>
    {{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</div>
  <div><span class="label">IVA (13%):</span>
    {{ frappe.utils.fmt_money(doc.sv_total_iva or 0, currency=doc.currency) }}</div>
  <div class="total-final"><span class="label">TOTAL:</span>
    {{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</div>
</div>

<div class="mh-info">
  <div><span class="label">Sello MH:</span>
    {{ doc.sv_sello_recepcion or "Pendiente de emisión" }}</div>
  <div><span class="label">Fecha Procesamiento:</span>
    {{ doc.sv_fecha_procesamiento or "—" }}</div>
</div>

{% if doc.sv_dte_qr_url %}
<div class="qr-section">
  <div><strong>Verificación en portal MH:</strong></div>
  <div style="margin-top:4px;">{{ doc.sv_dte_qr_url }}</div>
  <div class="qr-pending">(Imagen QR disponible en próxima versión)</div>
</div>
{% endif %}"""


def execute():
    if frappe.db.exists("Print Format", _NAME):
        pf = frappe.get_doc("Print Format", _NAME)
        pf.html = _HTML
        pf.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Print Format",
            "name": _NAME,
            "doc_type": "Sales Invoice",
            "module": "ERPNext Localization SV",
            "standard": "No",
            "custom_format": 1,
            "print_format_type": "Jinja",
            "html": _HTML,
        }).insert(ignore_permissions=True)
    frappe.db.commit()
