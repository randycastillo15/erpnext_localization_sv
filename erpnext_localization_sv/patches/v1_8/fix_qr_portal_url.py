"""
Patch v1.8 — Corrige URL del portal de consulta MH y actualiza Print Format.

Cambios:
  1. Configura url_verificacion_mh en SV DTE Settings con la URL correcta del portal
     admin.factura.gob.sv/consultaPublica (la URL anterior era incorrecta).
  2. Actualiza sv_dte_qr_url en Sales Invoices existentes que tenían la URL rota.
  3. Actualiza Print Format "DTE El Salvador": la sección QR ahora muestra el
     codigoGeneracion como "Código para verificar en portal MH" con instrucciones claras,
     en lugar de una URL parametrizada que no funciona.

Nota técnica: el portal MH (admin.factura.gob.sv/consultaPublica) es una SPA Angular
con ngOnInit(){} vacío — no lee query params de la URL. El usuario debe ingresar
el codigoGeneracion manualmente en el formulario del portal.

Idempotente: puede ejecutarse múltiples veces sin efecto colateral.
"""

import frappe

_PORTAL_URL = "https://admin.factura.gob.sv/consultaPublica"
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
  .qr-codigo { font-family: monospace; font-size: 9px; color: #333;
               background: #f5f5f5; padding: 3px 6px; border-radius: 3px;
               display: block; margin-top: 4px; }
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

{% if doc.sv_dte_generation_code and doc.sv_estado_mh == "PROCESADO" %}
<div class="qr-section">
  <div><strong>Verificación en portal Ministerio de Hacienda:</strong></div>
  <div style="margin-top:4px;">
    Ingrese el siguiente código en
    <strong>admin.factura.gob.sv/consultaPublica</strong>:
  </div>
  <span class="qr-codigo">{{ doc.sv_dte_generation_code }}</span>
  <div style="margin-top:4px; color:#888;">
    Fecha de emisión para el portal: {{ doc.posting_date }}
  </div>
</div>
{% endif %}"""


def execute():
    # 1. Configurar url_verificacion_mh con la URL correcta del portal MH.
    #    tabSingles no tiene UNIQUE constraint — limpiar primero para evitar duplicados.
    frappe.db.sql(
        "DELETE FROM `tabSingles` WHERE doctype=%s AND field=%s",
        ("SV DTE Settings", "url_verificacion_mh"),
    )
    frappe.db.sql(
        "INSERT INTO `tabSingles` (doctype, field, value) VALUES (%s, %s, %s)",
        ("SV DTE Settings", "url_verificacion_mh", _PORTAL_URL),
    )

    # 2. Corregir sv_dte_qr_url en Sales Invoices: reemplazar cualquier URL rota por la URL del portal
    #    Solo actualizar registros que tienen el campo poblado (tenían URL incorrecta antes)
    invoices_with_qr = frappe.db.get_all(
        "Sales Invoice",
        filters={"sv_dte_qr_url": ["!=", ""]},
        pluck="name",
    )
    for name in invoices_with_qr:
        frappe.db.set_value("Sales Invoice", name, "sv_dte_qr_url", _PORTAL_URL)

    # 3. Actualizar Print Format
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
