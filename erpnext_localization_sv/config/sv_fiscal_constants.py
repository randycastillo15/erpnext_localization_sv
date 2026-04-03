"""
Constantes técnicas fiscales para El Salvador — URLs, paths y tasas.

Los catálogos oficiales MH (tipos de documento, actividades, etc.)
están en config/sv_catalogs.py.
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
# ---------------------------------------------------------------------------
NIT_REGEX = r"^\d{4}-\d{6}-\d{3}-\d$"
NRC_REGEX = r"^\d{1,7}-\d$"

# ---------------------------------------------------------------------------
# Endpoints MH base (ambiente pruebas y producción)
# Override vía SV DTE Settings (DocType) o site_config.json.
# ---------------------------------------------------------------------------
MH_ENDPOINT_TEST = "https://apitest.dtes.mh.gob.sv"
MH_ENDPOINT_PROD = "https://api.dtes.mh.gob.sv"

# Rutas de API por servicio
MH_AUTH_PATH          = "/seguridad/auth"
MH_RECEIVE_PATH       = "/fesv/recepciondte"
MH_RECEIVE_BATCH_PATH = "/fesv/recepcionlote/"
MH_QUERY_DTE_PATH     = "/fesv/recepcion/consultadte/"
MH_QUERY_BATCH_PATH   = "/fesv/recepcion/consultadtelote/{codigo_lote}"
MH_CONTINGENCY_PATH   = "/fesv/contingencia"
MH_INVALIDATION_PATH  = "/fesv/anulardte"

MH_QR_URL = (
    "https://admin.factura.gob.sv/consultaPublica"
    "?ambiente={ambiente}&codGen={cod_gen}&fechaEmi={fecha_emi}"
)

# ---------------------------------------------------------------------------
# URL base del DTE Gateway local (FastAPI en :8100)
# Override posible via site_config.json → dte_gateway_url
#                      variable de entorno → DTE_GATEWAY_URL
# ---------------------------------------------------------------------------
DTE_GATEWAY_URL = "http://host.docker.internal:8100"
