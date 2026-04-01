"""
Constantes fiscales base para El Salvador.
Fuente: Ministerio de Hacienda — Ley de Impuesto a la Transferencia de Bienes
Muebles y a la Prestación de Servicios (Ley IVA) y normativa DTE.
"""

from decimal import Decimal

# ---------------------------------------------------------------------------
# País y moneda
# ---------------------------------------------------------------------------
DEFAULT_COUNTRY = "El Salvador"
DEFAULT_CURRENCY = "USD"

# ---------------------------------------------------------------------------
# Tasas fiscales
# ---------------------------------------------------------------------------
IVA_RATE = Decimal("0.13")  # 13 % — tasa estándar IVA

# ---------------------------------------------------------------------------
# Validación de identificadores fiscales
# Formato NIT:  DDDD-DDDDDD-DDD-D  (contribuyentes persona natural/jurídica)
# Formato NRC:  hasta 7 dígitos - 1 dígito verificador
# ---------------------------------------------------------------------------
NIT_REGEX = r"^\d{4}-\d{6}-\d{3}-\d$"
NRC_REGEX = r"^\d{1,7}-\d$"

# ---------------------------------------------------------------------------
# Tipos de documento DTE (catálogo oficial MH)
# Solo los más frecuentes en fase inicial.
# El catálogo completo se agregará en config/sv_dte_catalog.py cuando
# se implemente la emisión real.
# ---------------------------------------------------------------------------
DTE_DOCUMENT_TYPES: dict[str, str] = {
	"01": "Factura de Consumidor Final",
	"03": "Comprobante de Crédito Fiscal",
	"05": "Nota de Débito",
	"06": "Nota de Crédito",
	"07": "Comprobante de Retención",
	"11": "Factura de Exportación",
	"14": "Factura de Sujeto Excluido",
}

# ---------------------------------------------------------------------------
# Endpoints MH (ambiente de pruebas y producción)
# Los valores reales se configurarán en "SV DTE Settings" (DocType futuro).
# Estas constantes son el fallback de referencia.
# ---------------------------------------------------------------------------
MH_ENDPOINT_TEST = "https://apidtetest.mh.gob.sv"
MH_ENDPOINT_PROD = "https://apidte.mh.gob.sv"

# ---------------------------------------------------------------------------
# URL base del DTE Gateway local (FastAPI en :8100)
# Desde dentro de Docker, localhost apunta al contenedor — no al host.
# host.docker.internal resuelve al host en Docker Desktop (Linux/Mac/Win).
# Override posible via site_config.json  →  dte_gateway_url
#                      variable de entorno →  DTE_GATEWAY_URL
# ---------------------------------------------------------------------------
DTE_GATEWAY_URL = "http://host.docker.internal:8100"
