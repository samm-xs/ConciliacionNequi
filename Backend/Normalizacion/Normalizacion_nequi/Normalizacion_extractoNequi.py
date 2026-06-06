import pandas as pd
import re
import unicodedata
from tabulate import tabulate
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


CONCEPTOS_BANCO_NEQUI = [
    "al gravamen movimiento",
    "de intereses pago",
]

COLUMNAS_CONCEPTOS_BANCO = [
    "concepto",
    "cantidad movimientos",
    "valor total",
]


def quitar_tildes(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")

    return texto


def limpiar_nombre_nequi(descripcion):
    """
    Limpia la descripción del extracto Nequi.

    Ejemplos:
    'De JOSE DOMINGO CERON' -> 'ceron domingo jose'
    'RECIBI POR BRE-B DE: CLAUDIA' -> 'b bre claudia'
    'PLASTICAUCHO COLOMBIA SA' -> 'colombia plasticaucho'
    """

    if pd.isna(descripcion):
        return ""

    texto = str(descripcion).strip()

    # Quitar tildes
    texto = quitar_tildes(texto)

    # Pasar a minúsculas
    texto = texto.lower()

    # Eliminar únicamente estos textos/palabras
    texto = re.sub(r"^recibi\s+por\s+", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bde:\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^de\s+", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bsa\b", "", texto, flags=re.IGNORECASE)

    # Quitar signos raros, dejando letras, números y espacios
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)

    # Normalizar espacios
    texto = re.sub(r"\s+", " ", texto).strip()

    # Tokenizar
    tokens = texto.split()

    # Ordenar alfabéticamente
    tokens = sorted(tokens)

    return " ".join(tokens)


def normalizar_nequi(df):
    """
    Recibe el DataFrame crudo de Nequi y devuelve:

    id | fecha | nombre | valor
    """

    df_base = df.copy()

    columnas_necesarias = [
        "id",
        "Fecha del movimiento",
        "Descripción",
        "Valor",
    ]

    faltantes = [
        col for col in columnas_necesarias
        if col not in df_base.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias en el DataFrame: "
            + ", ".join(faltantes)
        )

    df_normalizado = pd.DataFrame()

    df_normalizado["id"] = df_base["id"]

    df_normalizado["fecha"] = pd.to_datetime(
        df_base["Fecha del movimiento"],
        errors="coerce"
    )

    df_normalizado["nombre"] = df_base["Descripción"].apply(
        limpiar_nombre_nequi
    )

    # El valor NO se toca
    df_normalizado["valor"] = df_base["Valor"]

    return df_normalizado


def separar_conceptos_banco_nequi(df_nequi_normalizado):
    """
    Separa conceptos bancarios informativos que no deben pasar por motores.

    Recibe el DataFrame normalizado con columnas:
    id | fecha | nombre | valor

    Devuelve:
    df_nequi_conciliable, df_conceptos_banco
    """

    df_base = df_nequi_normalizado.copy()

    columnas_necesarias = ["id", "fecha", "nombre", "valor"]
    faltantes = [
        columna for columna in columnas_necesarias
        if columna not in df_base.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias en el DataFrame normalizado: "
            + ", ".join(faltantes)
        )

    mascara_conceptos = df_base["nombre"].isin(CONCEPTOS_BANCO_NEQUI)
    df_conciliable = df_base[~mascara_conceptos].copy()
    df_conceptos = df_base[mascara_conceptos].copy()

    if df_conceptos.empty:
        return (
            df_conciliable,
            pd.DataFrame(columns=COLUMNAS_CONCEPTOS_BANCO),
        )

    df_resumen = (
        df_conceptos
        .groupby("nombre", as_index=False)
        .agg(
            **{
                "cantidad movimientos": ("id", "count"),
                "valor total": ("valor", "sum"),
            }
        )
        .rename(columns={"nombre": "concepto"})
    )

    return df_conciliable, df_resumen[COLUMNAS_CONCEPTOS_BANCO]
