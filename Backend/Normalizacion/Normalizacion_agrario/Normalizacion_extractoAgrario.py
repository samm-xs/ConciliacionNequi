import re
import unicodedata

import pandas as pd


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


def limpiar_nombre_agrario(descripcion):
    """
    Limpia la descripción del extracto Banco Agrario de forma conservadora.

    No elimina palabras bancarias todavía; solo normaliza el texto para que
    pueda compararse con el contrato actual del motor.
    """

    if pd.isna(descripcion):
        return ""

    texto = str(descripcion).strip()
    texto = quitar_tildes(texto)
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    tokens = texto.split()
    tokens = sorted(tokens)

    return " ".join(tokens)


def normalizar_agrario(df):
    """
    Recibe el DataFrame crudo de Banco Agrario y devuelve:

    id | fecha | nombre | valor
    """

    df_base = df.copy()

    columnas_necesarias = [
        "id",
        "fecha",
        "descripcion",
        "valor",
    ]

    faltantes = [
        col for col in columnas_necesarias
        if col not in df_base.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias en el DataFrame de Banco Agrario: "
            + ", ".join(faltantes)
        )

    df_normalizado = pd.DataFrame()

    df_normalizado["id"] = df_base["id"]
    df_normalizado["fecha"] = pd.to_datetime(
        df_base["fecha"],
        errors="coerce",
    )
    df_normalizado["nombre"] = df_base["descripcion"].apply(
        limpiar_nombre_agrario
    )
    df_normalizado["valor"] = df_base["valor"]

    return df_normalizado


def separar_conceptos_banco_agrario(df_agrario_normalizado):
    """
    Separa Banco Agrario en:

    - df_conciliable: solo movimientos con valor positivo.
    - df_resumen: todos los movimientos agrupados por nombre/concepto.
    """

    df_base = df_agrario_normalizado.copy()

    columnas_necesarias = ["id", "fecha", "nombre", "valor"]
    faltantes = [
        columna for columna in columnas_necesarias
        if columna not in df_base.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias en el DataFrame normalizado de Banco Agrario: "
            + ", ".join(faltantes)
        )

    valores_numericos = pd.to_numeric(df_base["valor"], errors="coerce")
    df_conciliable = df_base[valores_numericos > 0].copy()
    df_conciliable = df_conciliable[columnas_necesarias]

    df_resumen_base = df_base.copy()
    df_resumen_base["_valor_numerico"] = valores_numericos

    if df_resumen_base.empty:
        df_resumen = pd.DataFrame(columns=COLUMNAS_CONCEPTOS_BANCO)
    else:
        df_resumen = (
            df_resumen_base
            .groupby("nombre", as_index=False)
            .agg(
                **{
                    "cantidad movimientos": ("id", "count"),
                    "valor total": ("_valor_numerico", "sum"),
                }
            )
            .rename(columns={"nombre": "concepto"})
        )

    return df_conciliable, df_resumen[COLUMNAS_CONCEPTOS_BANCO]
