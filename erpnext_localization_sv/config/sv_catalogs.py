"""
Catálogos oficiales MH para El Salvador — CAT-001 a CAT-024.

Fuente: Ministerio de Hacienda, catálogos del Sistema de Transmisión DTE.
Solo se incluyen los catálogos necesarios para los tipos FE (01), CCF (03) y NC (05).
"""

# ---------------------------------------------------------------------------
# CAT-001 — Ambiente
# ---------------------------------------------------------------------------
CAT_001_AMBIENTE: dict[str, str] = {
    "00": "Pruebas",
    "01": "Producción",
}

# ---------------------------------------------------------------------------
# CAT-002 — Tipo de Documento Tributario Electrónico
# ---------------------------------------------------------------------------
CAT_002_TIPO_DTE: dict[str, str] = {
    "01": "Factura",
    "03": "Comprobante de Crédito Fiscal",
    "04": "Nota de Remisión",
    "05": "Nota de Crédito",
    "06": "Nota de Débito",
    "07": "Comprobante de Retención",
    "08": "Comprobante de Liquidación",
    "09": "Documento Contable de Liquidación",
    "11": "Factura de Exportación",
    "14": "Factura de Sujeto Excluido",
    "15": "Comprobante de Donación",
}

# Alias para los 3 del MVP
DTE_FE  = "01"
DTE_CCF = "03"
DTE_NC  = "05"

# ---------------------------------------------------------------------------
# CAT-003 — Modelo de Facturación
# ---------------------------------------------------------------------------
CAT_003_MODELO: dict[int, str] = {
    1: "Previo",
    2: "Diferido",
}

# ---------------------------------------------------------------------------
# CAT-004 — Tipo de Operación
# ---------------------------------------------------------------------------
CAT_004_OPERACION: dict[int, str] = {
    1: "Normal",
    2: "Contingencia",
}

# ---------------------------------------------------------------------------
# CAT-009 — Tipo de Ítem
# ---------------------------------------------------------------------------
CAT_009_TIPO_ITEM: dict[int, str] = {
    1: "Bienes",
    2: "Servicios",
    3: "Ambos",
    4: "Otros Tributos",
}

# ---------------------------------------------------------------------------
# CAT-012 — Departamento
# ---------------------------------------------------------------------------
CAT_012_DEPARTAMENTO: dict[str, str] = {
    "01": "Ahuachapán",
    "02": "Santa Ana",
    "03": "Sonsonate",
    "04": "Chalatenango",
    "05": "La Libertad",
    "06": "San Salvador",
    "07": "Cuscatlán",
    "08": "La Paz",
    "09": "Cabañas",
    "10": "San Vicente",
    "11": "Usulután",
    "12": "San Miguel",
    "13": "Morazán",
    "14": "La Unión",
}

# ---------------------------------------------------------------------------
# CAT-014 — Unidad de Medida (parcial — los más comunes)
# ---------------------------------------------------------------------------
CAT_014_UNIDAD_MEDIDA: dict[int, str] = {
    59:  "Unidad",
    2:   "Kilogramo",
    3:   "Gramo",
    10:  "Litro",
    11:  "Mililitro",
    21:  "Metro",
    27:  "Metro cuadrado",
    28:  "Metro cúbico",
    99:  "Otra",
}

# ---------------------------------------------------------------------------
# CAT-016 — Condición de la Operación
# ---------------------------------------------------------------------------
CAT_016_CONDICION_OPERACION: dict[int, str] = {
    1: "Contado",
    2: "Al crédito",
    3: "Otro",
}

# ---------------------------------------------------------------------------
# CAT-017 — Tipo de Establecimiento
# ---------------------------------------------------------------------------
CAT_017_TIPO_ESTABLECIMIENTO: dict[str, str] = {
    "01": "Sucursal/Agencia",
    "02": "Casa Matriz",
    "04": "Bodega",
    "07": "Patio",
    "20": "Otros",
}

# ---------------------------------------------------------------------------
# CAT-022 — Tipo de Documento de Identificación del Receptor
# ---------------------------------------------------------------------------
CAT_022_TIPO_DOC_IDENTIFICACION: dict[str, str] = {
    "13": "DUI",
    "02": "NIT",
    "03": "Pasaporte",
    "36": "NRC",
    "37": "Otro",
}

# ---------------------------------------------------------------------------
# Acceso unificado por código de catálogo
# ---------------------------------------------------------------------------
CATALOGS: dict[str, dict] = {
    "CAT-001": CAT_001_AMBIENTE,
    "CAT-002": CAT_002_TIPO_DTE,
    "CAT-003": CAT_003_MODELO,
    "CAT-004": CAT_004_OPERACION,
    "CAT-009": CAT_009_TIPO_ITEM,
    "CAT-012": CAT_012_DEPARTAMENTO,
    "CAT-014": CAT_014_UNIDAD_MEDIDA,
    "CAT-016": CAT_016_CONDICION_OPERACION,
    "CAT-017": CAT_017_TIPO_ESTABLECIMIENTO,
    "CAT-022": CAT_022_TIPO_DOC_IDENTIFICACION,
}


def get_catalog(cat_code: str) -> dict:
    """Retorna el diccionario de un catálogo por su código (ej. 'CAT-002')."""
    return CATALOGS.get(cat_code, {})


def get_label(cat_code: str, key) -> str | None:
    """Retorna la descripción de una clave dentro de un catálogo."""
    return CATALOGS.get(cat_code, {}).get(key)
