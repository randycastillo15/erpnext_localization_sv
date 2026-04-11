"""
Patch v1.27 — URL parametrizada MH + QR en Print Format DTE.

Cambios:
  1. Backfill sv_dte_qr_url en Sales Invoices existentes:
     URL base → URL completa con ?ambiente=XX&codGen=UUID&fechaEmi=YYYY-MM-DD
  2. Actualizar Print Format "DTE El Salvador":
     - QR code real (api.qrserver.com) en esquina superior derecha
     - Layout inspirado en PDF oficial MH: Emisor|Receptor, Items con Código, Sumas completas
     - Sección Detalles con condición de operación y observaciones

Contexto:
  El portal admin.factura.gob.sv/consultaPublica SÍ acepta query params para pre-llenar
  el formulario de consulta. Los comentarios anteriores que decían lo contrario eran incorrectos.
  La constante MH_QR_URL en sv_fiscal_constants.py ya tenía el formato correcto.
"""

import frappe

_NAME = "DTE El Salvador"

_HTML = """{%- set tipo_map = {
    "FE":  "Factura Electrónica (01)",
    "CCF": "Comprobante de Crédito Fiscal (03)",
    "NC":  "Nota de Crédito (05)",
    "ND":  "Nota de Débito (06)"
} -%}
{%- set _s = frappe.get_single("SV DTE Settings") -%}
{%- set _co = frappe.get_doc("Company", doc.company) -%}
{#- Datos del establecimiento por defecto (defensivo) -#}
{%- set _estab_name = _s.get("establecimiento_default") or "" -%}
{%- set _estab = frappe.get_doc("SV DTE Establishment", _estab_name) if _estab_name and frappe.db.exists("SV DTE Establishment", _estab_name) else None -%}
{#- URL QR: codificar la URL del portal para usarla como parámetro de qrserver -#}
{%- set _qr_enc = (doc.sv_dte_qr_url or "")
    | replace("://", "%3A%2F%2F")
    | replace("/", "%2F")
    | replace("?", "%3F")
    | replace("&", "%26")
    | replace("=", "%3D")
-%}
<style>
  body { font-family: Arial, sans-serif; font-size: 11px; margin: 0; padding: 16px; color: #111; }

  /* ── Header ── */
  .dte-header { display: table; width: 100%; margin-bottom: 10px; border-bottom: 2px solid #222; padding-bottom: 8px; }
  .dte-header-left  { display: table-cell; vertical-align: middle; }
  .dte-header-right { display: table-cell; vertical-align: middle; text-align: right; width: 130px; }
  .dte-title  { font-size: 14px; font-weight: bold; text-transform: uppercase; }
  .dte-tipo   { font-size: 12px; font-weight: bold; color: #333; margin-top: 2px; }
  .dte-company { font-size: 10px; color: #555; margin-top: 2px; }

  /* ── Info DTE ── */
  .dte-info { margin-bottom: 10px; }
  .dte-info table { width: 100%; border-collapse: collapse; }
  .dte-info td { padding: 2px 8px 2px 0; vertical-align: top; font-size: 10px; }
  .dte-info td:nth-child(odd) { font-weight: bold; white-space: nowrap; width: 30%; }

  /* ── Emisor / Receptor ── */
  .partes { display: table; width: 100%; margin-bottom: 10px; border-collapse: collapse; }
  .parte  { display: table-cell; width: 50%; vertical-align: top; border: 1px solid #ccc; padding: 6px 8px; }
  .parte-header {
    font-weight: bold; font-size: 10px; letter-spacing: 0.5px;
    background: #1a56db; color: #fff; padding: 3px 6px; margin: -6px -8px 6px -8px;
    text-transform: uppercase;
  }
  .parte-sep { display: table-cell; width: 6px; }
  .parte p { margin: 1px 0; font-size: 10px; line-height: 1.4; }
  .parte .label { font-weight: bold; }

  /* ── Tabla de items ── */
  table.items { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10px; }
  table.items th { background: #1a56db; color: #fff; padding: 4px 6px; text-align: left; }
  table.items td { border: 1px solid #ddd; padding: 3px 6px; vertical-align: top; }
  table.items tr:nth-child(even) td { background: #f8f9ff; }

  /* ── Detalles + Sumas ── */
  .bottom { display: table; width: 100%; margin-top: 10px; border-collapse: collapse; }
  .bottom-left  { display: table-cell; width: 50%; vertical-align: top; padding-right: 8px; }
  .bottom-right { display: table-cell; width: 50%; vertical-align: top; border: 1px solid #ccc; padding: 6px 8px; }
  .section-header {
    font-weight: bold; font-size: 10px; background: #1a56db; color: #fff;
    padding: 3px 6px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .suma-row { display: table; width: 100%; font-size: 10px; margin-bottom: 1px; }
  .suma-label { display: table-cell; }
  .suma-value { display: table-cell; text-align: right; white-space: nowrap; font-family: monospace; }
  .suma-total { font-weight: bold; border-top: 1px solid #999; margin-top: 4px; padding-top: 3px; font-size: 11px; }
  .detail-p { font-size: 10px; margin: 2px 0; line-height: 1.5; }

  /* ── Info MH (sello) ── */
  .mh-info { margin-top: 10px; padding: 6px 8px; border: 1px solid #ddd;
             background: #fafafa; font-size: 9px; line-height: 1.6; word-break: break-all; }
</style>

<!-- ═══ HEADER ═══ -->
<div class="dte-header">
  <div class="dte-header-left">
    <div class="dte-title">Documento Tributario Electrónico</div>
    <div class="dte-tipo">{{ tipo_map.get(doc.sv_dte_document_type, doc.sv_dte_document_type or "DTE") }}</div>
    <div class="dte-company">{{ _co.company_name or doc.company }}</div>
  </div>
  <div class="dte-header-right">
    {%- if doc.sv_dte_qr_url and "codGen=" in doc.sv_dte_qr_url -%}
    <img src="https://api.qrserver.com/v1/create-qr-code/?size=110x110&data={{ _qr_enc }}"
         width="110" height="110" alt="QR MH" style="display:block;margin-left:auto;"/>
    {%- endif -%}
  </div>
</div>

<!-- ═══ INFO DTE ═══ -->
<div class="dte-info">
  <table>
    <tr>
      <td>Código de Generación:</td>
      <td style="word-break:break-all;">{{ doc.sv_dte_generation_code or "—" }}</td>
      <td>Modelo de facturación:</td>
      <td>Modelo de facturación previa</td>
    </tr>
    <tr>
      <td>Número de Control:</td>
      <td>{{ doc.sv_dte_control_number or "—" }}</td>
      <td>Tipo de transmisión:</td>
      <td>Transmisión normal</td>
    </tr>
    <tr>
      <td>Sello de recepción:</td>
      <td style="word-break:break-all;">{{ doc.sv_sello_recepcion or "Pendiente" }}</td>
      <td>Fecha y hora de generación:</td>
      <td>{{ doc.sv_dte_sent_at or doc.posting_date }}</td>
    </tr>
  </table>
</div>

<hr style="border:none;border-top:1px solid #ccc;margin:8px 0;"/>

<!-- ═══ EMISOR | RECEPTOR ═══ -->
<div class="partes">
  <!-- EMISOR -->
  <div class="parte">
    <div class="parte-header">Emisor</div>
    <p><span class="label">Nombre:</span> {{ _s.get("nombre_emisor") or _co.company_name or doc.company }}</p>
    {%- if _s.get("nit_emisor") %}<p><span class="label">NIT:</span> {{ _s.get("nit_emisor") }}</p>{%- endif %}
    {%- if _s.get("nrc_emisor") %}<p><span class="label">NRC:</span> {{ _s.get("nrc_emisor") }}</p>{%- endif %}
    {%- if _s.get("desc_actividad") %}<p><span class="label">Actividad económica:</span> {{ _s.get("desc_actividad") }}</p>{%- endif %}
    {%- if _estab and _estab.get("complemento") %}<p><span class="label">Dirección:</span> {{ _estab.get("complemento") }}</p>{%- endif %}
    {%- if _estab and _estab.get("telefono") %}<p><span class="label">Teléfono:</span> {{ _estab.get("telefono") }}</p>{%- endif %}
    {%- if _estab and _estab.get("correo") %}<p><span class="label">Correo:</span> {{ _estab.get("correo") }}</p>{%- endif %}
    {%- if _s.get("nombre_comercial") %}<p><span class="label">Nombre comercial:</span> {{ _s.get("nombre_comercial") }}</p>{%- endif %}
    {%- if _estab %}<p><span class="label">Establecimiento:</span> {{ _estab.get("tipo_establecimiento") or "Casa matriz" }}</p>{%- endif %}
  </div>
  <div class="parte-sep"></div>
  <!-- RECEPTOR -->
  <div class="parte">
    <div class="parte-header">Receptor</div>
    <p><span class="label">Nombre o Razón Social:</span> {{ doc.customer_name }}</p>
    {%- if doc.sv_dte_document_type in ("CCF", "NC", "ND") and doc.customer -%}
    {%- set _c = frappe.get_doc("Customer", doc.customer) -%}
    {%- if _c.sv_nit %}<p><span class="label">NIT:</span> {{ _c.sv_nit }}</p>{%- endif %}
    {%- if _c.sv_nrc %}<p><span class="label">NRC:</span> {{ _c.sv_nrc }}</p>{%- endif %}
    {%- if _c.sv_desc_actividad %}<p><span class="label">Actividad económica:</span> {{ _c.sv_desc_actividad }}</p>{%- endif %}
    {%- if _c.sv_nombre_comercial %}<p><span class="label">Nombre comercial:</span> {{ _c.sv_nombre_comercial }}</p>{%- endif %}
    {%- if _c.sv_direccion_complemento %}<p><span class="label">Dirección:</span> {{ _c.sv_direccion_complemento }}</p>{%- endif %}
    {%- if _c.sv_telefono %}<p><span class="label">Teléfono:</span> {{ _c.sv_telefono }}</p>{%- endif %}
    {%- if _c.sv_correo %}<p><span class="label">Correo:</span> {{ _c.sv_correo }}</p>{%- endif %}
    {%- endif %}
  </div>
</div>

<!-- ═══ ITEMS ═══ -->
<table class="items">
  <thead>
    <tr>
      <th style="width:4%;">N°</th>
      <th style="width:10%;">Código</th>
      <th style="width:8%;">Cant.</th>
      <th>Descripción</th>
      <th style="width:14%;text-align:right;">Precio Unitario</th>
      <th style="width:12%;text-align:right;">Total</th>
    </tr>
  </thead>
  <tbody>
    {% for item in doc.items %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ item.item_code or "—" }}</td>
      <td>{{ item.qty }}</td>
      <td>{{ item.item_name }}</td>
      <td style="text-align:right;">{{ frappe.utils.fmt_money(item.rate, currency=doc.currency) }}</td>
      <td style="text-align:right;">{{ frappe.utils.fmt_money(item.amount, currency=doc.currency) }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<!-- ═══ DETALLES | SUMAS ═══ -->
<div class="bottom">
  <!-- DETALLES -->
  <div class="bottom-left">
    <div class="section-header">Detalles</div>
    {%- if doc.sv_observaciones_mh and doc.sv_observaciones_mh != "[]" %}
    <p class="detail-p"><span class="label">Observación:</span> {{ doc.sv_observaciones_mh | replace("[", "") | replace("]", "") | replace('"', '') }}</p>
    {%- else %}
    <p class="detail-p"><span class="label">Observación:</span></p>
    {%- endif %}
    <p class="detail-p"><span class="label">Condición de la operación:</span>
      {%- if doc.payment_terms_template %} {{ doc.payment_terms_template }}
      {%- elif doc.due_date == doc.posting_date %} Contado
      {%- else %} Crédito
      {%- endif %}
    </p>
    <p class="detail-p" style="margin-top:8px;"><span class="label">Responsable por parte del emisor:</span></p>
    <p class="detail-p"><span class="label">Responsable por parte del receptor:</span></p>
  </div>
  <!-- SUMAS -->
  <div class="bottom-right">
    <div class="section-header" style="margin:-6px -8px 6px -8px;">Sumas</div>
    {%- set _gravado = doc.net_total or 0 %}
    {%- set _descuento = doc.discount_amount or 0 %}
    {%- set _iva = doc.sv_total_iva or 0 %}
    {%- set _total = doc.grand_total or 0 %}
    <div class="suma-row"><span class="suma-label">Ventas no sujetas:</span><span class="suma-value">$ 0.00</span></div>
    <div class="suma-row"><span class="suma-label">Total gravado:</span><span class="suma-value">{{ frappe.utils.fmt_money(_gravado, currency=doc.currency) }}</span></div>
    <div class="suma-row"><span class="suma-label">Monto global descuentos:</span><span class="suma-value">{{ frappe.utils.fmt_money(_descuento, currency=doc.currency) }}</span></div>
    <div class="suma-row"><span class="suma-label">Sumatoria de ventas:</span><span class="suma-value">{{ frappe.utils.fmt_money(_gravado - _descuento, currency=doc.currency) }}</span></div>
    <div class="suma-row"><span class="suma-label">Impuesto al valor agregado (13%):</span><span class="suma-value">{{ frappe.utils.fmt_money(_iva, currency=doc.currency) }}</span></div>
    <div class="suma-row"><span class="suma-label">IVA percibido:</span><span class="suma-value">$ 0.00</span></div>
    <div class="suma-row"><span class="suma-label">IVA retenido:</span><span class="suma-value">$ 0.00</span></div>
    <div class="suma-row"><span class="suma-label">Retención renta:</span><span class="suma-value">$ 0.00</span></div>
    <div class="suma-row"><span class="suma-label">Monto total de la operación:</span><span class="suma-value">{{ frappe.utils.fmt_money(_total, currency=doc.currency) }}</span></div>
    <div class="suma-row"><span class="suma-label">Total otros montos no afectos:</span><span class="suma-value">$ 0.00</span></div>
    <div class="suma-row suma-total"><span class="suma-label">Total a pagar:</span><span class="suma-value">{{ frappe.utils.fmt_money(_total, currency=doc.currency) }}</span></div>
  </div>
</div>

<!-- ═══ INFO MH ═══ -->
<div class="mh-info">
  <strong>Sello MH:</strong> {{ doc.sv_sello_recepcion or "Pendiente de emisión" }}<br/>
  <strong>Fecha Procesamiento:</strong> {{ doc.sv_fecha_procesamiento or "—" }}&nbsp;&nbsp;
  <strong>Estado:</strong> {{ doc.sv_estado_mh or "—" }}
</div>"""


def execute() -> None:
    # ── 1. Backfill sv_dte_qr_url en facturas existentes ─────────────────────
    from erpnext_localization_sv.config.sv_fiscal_constants import MH_QR_URL

    try:
        _settings = frappe.get_single("SV DTE Settings")
        _ambiente = _settings.get("ambiente") or "00"
    except Exception:
        _ambiente = "00"

    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters={"sv_dte_generation_code": ["!=", ""]},
        fields=["name", "sv_dte_generation_code", "posting_date", "sv_dte_qr_url"],
    )
    updated = 0
    for inv in invoices:
        if not inv.sv_dte_generation_code:
            continue
        if "codGen=" in (inv.sv_dte_qr_url or ""):
            continue  # ya tiene URL completa
        new_url = MH_QR_URL.format(
            ambiente=_ambiente,
            cod_gen=inv.sv_dte_generation_code,
            fecha_emi=str(inv.posting_date),
        )
        frappe.db.set_value("Sales Invoice", inv.name, {
            "sv_dte_qr_url":      new_url,
            "sv_dte_environment": _ambiente,
        })
        updated += 1

    frappe.db.commit()
    frappe.logger().info(f"[v1_27] sv_dte_qr_url actualizado en {updated} facturas")

    # ── 2. Actualizar Print Format "DTE El Salvador" ──────────────────────────
    if frappe.db.exists("Print Format", _NAME):
        pf = frappe.get_doc("Print Format", _NAME)
        pf.html = _HTML
        pf.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype":           "Print Format",
            "name":              _NAME,
            "doc_type":          "Sales Invoice",
            "module":            "ERPNext Localization SV",
            "standard":          "No",
            "custom_format":     1,
            "print_format_type": "Jinja",
            "html":              _HTML,
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.logger().info("[v1_27] Print Format 'DTE El Salvador' actualizado con QR y layout mejorado")
