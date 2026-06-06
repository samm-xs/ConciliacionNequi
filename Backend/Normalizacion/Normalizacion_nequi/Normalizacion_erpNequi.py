import pandas as pd
import re
import unicodedata
from tabulate import tabulate
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def quitar_tildes(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")

    return texto


def limpiar_nombre_erp(nombre):
    """
    Limpia y ordena alfabéticamente el nombre.

    Ejemplos:
    'ORDOÑEZ JACANAMEJOY' -> 'jacanamejoy ordonez'
    'PATIÑO HERMES ANTONI' -> 'antoni hermes patino'
    'DISTRIBUCIONES AXA SA' -> 'axa distribuciones'
    """

    if pd.isna(nombre):
        return ""

    texto = str(nombre).strip()

    # Quitar tildes
    texto = quitar_tildes(texto)

    # Pasar a minúsculas
    texto = texto.lower()

    # Eliminar únicamente estos textos/palabras
    texto = re.sub(r"^recibi\s+por\s+bre-b\s+de:\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^de\s+", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bsa\b", "", texto, flags=re.IGNORECASE)

    # Quitar signos raros, dejando letras, números y espacios
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)

    # Normalizar espacios
    texto = re.sub(r"\s+", " ", texto).strip()

    # Tokenizar y ordenar alfabéticamente
    tokens = texto.split()
    tokens = sorted(tokens)

    return " ".join(tokens)


def unir_debito_credito(debito, credito):
    """
    Une debitos y creditos en una sola columna valor.

    - debitos quedan positivos
    - creditos quedan negativos
    """

    if pd.notna(debito):
        return debito

    if pd.notna(credito):
        return -credito

    return None


def normalizar_erp_nequi(df):
    """
    Recibe el DataFrame crudo del ERP y devuelve:

    id | fecha | nombre | valor
    """

    df_base = df.copy()

    columnas_necesarias = [
        "id",
        "fecha",
        "nombre_tercero",
        "debitos",
        "creditos",
    ]

    faltantes = [
        col for col in columnas_necesarias
        if col not in df_base.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias en el DataFrame del ERP: "
            + ", ".join(faltantes)
        )

    df_normalizado = pd.DataFrame()

    df_normalizado["id"] = df_base["id"]

    df_normalizado["fecha"] = pd.to_datetime(
        df_base["fecha"],
        errors="coerce"
    )

    df_normalizado["nombre"] = df_base["nombre_tercero"].apply(
        limpiar_nombre_erp
    )

    df_normalizado["valor"] = df_base.apply(
        lambda fila: unir_debito_credito(
            fila["debitos"],
            fila["creditos"]
        ),
        axis=1
    )

    return df_normalizado