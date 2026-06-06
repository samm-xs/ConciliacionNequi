from decimal import Decimal, InvalidOperation
import re

import pandas as pd


PUNTAJE_FECHA = 70
PUNTAJE_TOKEN_NOMBRE = 10
PUNTAJE_NOMBRE_MAXIMO = 30

SCORE_VALOR_NO_APLICA = 0

ESTADOS_USAN_ERP = ["conciliado", "por_revisar"]


# ============================================================
# VALIDACIONES Y NORMALIZACIÓN MÍNIMA
# ============================================================

def validar_dataframe(df, nombre_df):
    columnas_necesarias = ["id", "fecha", "nombre", "valor"]

    faltantes = [
        columna for columna in columnas_necesarias
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Al DataFrame {nombre_df} le faltan columnas: "
            + ", ".join(faltantes)
        )


def normalizar_valor_contable(valor):
    """
    Convierte un valor a Decimal para comparación contable exacta.

    No aplica tolerancias: dos valores solo coinciden si su representación
    decimal es exactamente equivalente.
    """

    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto == "":
        return None

    texto = texto.replace("$", "").replace(",", "").strip()

    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError):
        return None


def preparar_dataframe(df):
    df_preparado = df.copy()

    df_preparado["fecha"] = pd.to_datetime(
        df_preparado["fecha"],
        errors="coerce"
    )

    df_preparado["_valor_clave"] = df_preparado["valor"].apply(
        normalizar_valor_contable
    )

    return df_preparado


def valores_iguales(valor_banco, valor_erp):
    valor_banco = normalizar_valor_contable(valor_banco)
    valor_erp = normalizar_valor_contable(valor_erp)

    if valor_banco is None or valor_erp is None:
        return False

    return valor_banco == valor_erp


def fechas_iguales(fecha_banco, fecha_erp):
    if pd.isna(fecha_banco) or pd.isna(fecha_erp):
        return False

    fecha_banco = pd.to_datetime(fecha_banco, errors="coerce")
    fecha_erp = pd.to_datetime(fecha_erp, errors="coerce")

    if pd.isna(fecha_banco) or pd.isna(fecha_erp):
        return False

    return fecha_banco.date() == fecha_erp.date()


def obtener_tokens_nombre(nombre):
    if pd.isna(nombre):
        return set()

    texto = str(nombre).lower().strip()
    tokens = re.findall(r"[a-z0-9]+", texto)

    return {
        token
        for token in tokens
        if len(token) > 1
    }


def calcular_score_nombre(nombre_banco, nombre_erp):
    tokens_banco = obtener_tokens_nombre(nombre_banco)
    tokens_erp = obtener_tokens_nombre(nombre_erp)

    tokens_comunes = tokens_banco.intersection(tokens_erp)
    cantidad_tokens = len(tokens_comunes)

    score_nombre = min(
        cantidad_tokens * PUNTAJE_TOKEN_NOMBRE,
        PUNTAJE_NOMBRE_MAXIMO
    )

    return score_nombre, sorted(tokens_comunes)


# ============================================================
# FASE 1: CONSTRUIR MATRIZ DE SCORING
# ============================================================

def construir_indice_erp_por_valor(df_erp):
    indice = {}

    for _, erp in df_erp.iterrows():
        valor_clave = erp["_valor_clave"]

        if valor_clave is None:
            continue

        indice.setdefault(valor_clave, []).append(erp)

    return indice


def columnas_matriz():
    return [
        "id_banco",
        "id_erp",
        "fecha_banco",
        "fecha_erp",
        "nombre_banco",
        "nombre_erp",
        "valor_banco",
        "valor_erp",
        "match_valor",
        "match_fecha",
        "match_nombre",
        "tokens_nombre_comunes",
        "score_valor",
        "score_fecha",
        "score_nombre",
        "score_total",
    ]


def construir_matriz_scoring(df_banco, df_erp):
    """
    Construye una matriz explícita de candidatos Banco vs ERP.

    Recibe DataFrames normalizados con columnas:
    id | fecha | nombre | valor

    El valor exacto es filtro obligatorio. La matriz solo contiene
    candidatos contablemente posibles: Banco.valor == ERP.valor.
    """

    validar_dataframe(df_banco, "BANCO")
    validar_dataframe(df_erp, "ERP")

    df_banco = preparar_dataframe(df_banco)
    df_erp = preparar_dataframe(df_erp)

    indice_erp_por_valor = construir_indice_erp_por_valor(df_erp)
    filas_matriz = []

    for _, banco in df_banco.iterrows():
        valor_clave = banco["_valor_clave"]

        if valor_clave is None:
            continue

        candidatos_erp = indice_erp_por_valor.get(valor_clave, [])

        for erp in candidatos_erp:
            match_fecha = fechas_iguales(
                banco["fecha"],
                erp["fecha"]
            )

            score_nombre, tokens_comunes = calcular_score_nombre(
                banco["nombre"],
                erp["nombre"]
            )

            score_fecha = PUNTAJE_FECHA if match_fecha else 0
            score_total = score_fecha + score_nombre

            filas_matriz.append({
                "id_banco": banco["id"],
                "id_erp": erp["id"],

                "fecha_banco": banco["fecha"],
                "fecha_erp": erp["fecha"],

                "nombre_banco": banco["nombre"],
                "nombre_erp": erp["nombre"],

                "valor_banco": banco["valor"],
                "valor_erp": erp["valor"],

                "match_valor": True,
                "match_fecha": match_fecha,
                "match_nombre": score_nombre > 0,
                "tokens_nombre_comunes": tokens_comunes,

                "score_valor": SCORE_VALOR_NO_APLICA,
                "score_fecha": score_fecha,
                "score_nombre": score_nombre,
                "score_total": score_total,
            })

    return pd.DataFrame(filas_matriz, columns=columnas_matriz())


# ============================================================
# FASE 2: RESOLVER CONCILIACIÓN DESDE LA MATRIZ
# ============================================================

def construir_fila_resultado(
    id_banco=None,
    id_erp=None,
    fecha_banco=None,
    fecha_erp=None,
    nombre_banco=None,
    nombre_erp=None,
    valor_banco=None,
    valor_erp=None,
    score_total=0,
    score_valor=SCORE_VALOR_NO_APLICA,
    score_fecha=0,
    score_nombre=0,
    estado="",
    observacion="",
):
    return {
        "id_banco": id_banco,
        "id_erp": id_erp,

        "fecha_banco": fecha_banco,
        "fecha_erp": fecha_erp,

        "nombre_banco": nombre_banco,
        "nombre_erp": nombre_erp,

        "valor_banco": valor_banco,
        "valor_erp": valor_erp,

        "score_valor": score_valor,
        "score_fecha": score_fecha,
        "score_nombre": score_nombre,
        "score_total": score_total,

        "estado": estado,
        "observacion": observacion,
    }


def obtener_registro_por_id(df, id_registro):
    encontrado = df[df["id"] == id_registro]

    if encontrado.empty:
        return None

    return encontrado.iloc[0]


def resolver_estado_candidato(candidato):
    """
    Decide el estado para un único mejor candidato Banco -> ERP.

    El valor ya coincidió por filtro duro. La fecha exacta permite
    conciliación automática cuando el candidato ganador es único.
    """

    if bool(candidato["match_fecha"]):
        return "conciliado", "Conciliación automática por valor y fecha exactos."

    if candidato["score_nombre"] > 0:
        return "por_revisar", "Valor exacto con pista parcial por nombre. Requiere revisión."

    return "por_revisar", "Solo coincide el valor exacto. Requiere revisión."


def construir_resultado_ambiguo_por_banco(reg_banco, mejores, mejor_score):
    ids_posibles = mejores["id_erp"].astype(str).tolist()

    return construir_fila_resultado(
        id_banco=reg_banco["id"],
        fecha_banco=reg_banco["fecha"],
        nombre_banco=reg_banco["nombre"],
        valor_banco=reg_banco["valor"],
        score_total=mejor_score,
        score_valor=SCORE_VALOR_NO_APLICA,
        score_fecha=mejores.iloc[0]["score_fecha"],
        score_nombre=mejores.iloc[0]["score_nombre"],
        estado="ambiguo",
        observacion=(
            "Varios candidatos ERP tienen el mismo mejor score. "
            "Posibles id_erp: " + ", ".join(ids_posibles)
        )
    )


def construir_resultado_desde_candidato(candidato):
    estado, observacion = resolver_estado_candidato(candidato)

    return construir_fila_resultado(
        id_banco=candidato["id_banco"],
        id_erp=candidato["id_erp"],

        fecha_banco=candidato["fecha_banco"],
        fecha_erp=candidato["fecha_erp"],

        nombre_banco=candidato["nombre_banco"],
        nombre_erp=candidato["nombre_erp"],

        valor_banco=candidato["valor_banco"],
        valor_erp=candidato["valor_erp"],

        score_valor=candidato["score_valor"],
        score_fecha=candidato["score_fecha"],
        score_nombre=candidato["score_nombre"],
        score_total=candidato["score_total"],

        estado=estado,
        observacion=observacion,
    )


def resolver_candidatos_por_banco(matriz, df_banco):
    resultados = []

    for _, reg_banco in df_banco.iterrows():
        candidatos = matriz[matriz["id_banco"] == reg_banco["id"]].copy()

        if candidatos.empty:
            resultados.append(
                construir_fila_resultado(
                    id_banco=reg_banco["id"],
                    fecha_banco=reg_banco["fecha"],
                    nombre_banco=reg_banco["nombre"],
                    valor_banco=reg_banco["valor"],
                    estado="huerfano_banco",
                    observacion="No se encontró ningún ERP con el mismo valor exacto."
                )
            )
            continue

        mejor_score = candidatos["score_total"].max()

        mejores = candidatos[
            candidatos["score_total"] == mejor_score
        ].copy()

        if len(mejores) > 1:
            resultados.append(
                construir_resultado_ambiguo_por_banco(
                    reg_banco=reg_banco,
                    mejores=mejores,
                    mejor_score=mejor_score
                )
            )
            continue

        resultados.append(
            construir_resultado_desde_candidato(mejores.iloc[0])
        )

    return pd.DataFrame(resultados, columns=columnas_resultado())


def resolver_conflictos_uno_a_uno(df_resultado):
    df_resuelto = df_resultado.copy()

    mascara_con_erp = (
        df_resuelto["id_erp"].notna()
        & df_resuelto["estado"].isin(ESTADOS_USAN_ERP)
    )

    ids_erp_repetidos = (
        df_resuelto[mascara_con_erp]
        .groupby("id_erp")
        .size()
    )

    ids_erp_repetidos = ids_erp_repetidos[
        ids_erp_repetidos > 1
    ].index.tolist()

    for id_erp in ids_erp_repetidos:
        mascara_conflicto = (
            df_resuelto["id_erp"].eq(id_erp)
            & df_resuelto["estado"].isin(ESTADOS_USAN_ERP)
        )

        candidatos = df_resuelto[mascara_conflicto].copy()
        mejor_score = candidatos["score_total"].max()
        mejores = candidatos[candidatos["score_total"] == mejor_score]

        if len(mejores) > 1:
            indices_empatados = mejores.index

            df_resuelto.loc[indices_empatados, "estado"] = "ambiguo"
            df_resuelto.loc[indices_empatados, "observacion"] = (
                "Conflicto uno-a-uno: varios bancos apuntan al mismo ERP "
                "con el mismo score."
            )

            indices_perdedores = candidatos.index.difference(indices_empatados)
        else:
            indice_ganador = mejores.index[0]

            df_resuelto.loc[indice_ganador, "observacion"] = (
                str(df_resuelto.loc[indice_ganador, "observacion"])
                + " Ganó conflicto uno-a-uno por mayor score."
            )

            indices_perdedores = candidatos.index.difference([indice_ganador])

        if len(indices_perdedores) > 0:
            df_resuelto.loc[indices_perdedores, "estado"] = "huerfano_banco"
            df_resuelto.loc[indices_perdedores, "id_erp"] = None
            df_resuelto.loc[indices_perdedores, "fecha_erp"] = None
            df_resuelto.loc[indices_perdedores, "nombre_erp"] = None
            df_resuelto.loc[indices_perdedores, "valor_erp"] = None
            df_resuelto.loc[indices_perdedores, "observacion"] = (
                "El ERP candidato fue asignado a otro banco con mayor score."
            )

    return df_resuelto


def agregar_huerfanos_erp(df_resultado, df_erp):
    ids_erp_usados = set(
        df_resultado.loc[
            df_resultado["id_erp"].notna()
            & df_resultado["estado"].isin(ESTADOS_USAN_ERP),
            "id_erp"
        ].tolist()
    )

    filas_huerfanos_erp = []

    for _, reg_erp in df_erp.iterrows():
        if reg_erp["id"] not in ids_erp_usados:
            filas_huerfanos_erp.append(
                construir_fila_resultado(
                    id_erp=reg_erp["id"],
                    fecha_erp=reg_erp["fecha"],
                    nombre_erp=reg_erp["nombre"],
                    valor_erp=reg_erp["valor"],
                    estado="huerfano_erp",
                    observacion="Registro ERP no conciliado con banco."
                )
            )

    if not filas_huerfanos_erp:
        return df_resultado

    return pd.concat(
        [
            df_resultado,
            pd.DataFrame(filas_huerfanos_erp)
        ],
        ignore_index=True
    )


def columnas_resultado():
    return [
        "id_banco",
        "id_erp",
        "fecha_banco",
        "fecha_erp",
        "nombre_banco",
        "nombre_erp",
        "valor_banco",
        "valor_erp",
        "score_valor",
        "score_fecha",
        "score_nombre",
        "score_total",
        "estado",
        "observacion",
    ]


def resolver_conciliacion_desde_matriz(matriz, df_banco, df_erp):
    """
    Toma la matriz de scoring y devuelve un único DataFrame resultado.

    Estados:
    - conciliado
    - por_revisar
    - ambiguo
    - huerfano_banco
    - huerfano_erp
    """

    validar_dataframe(df_banco, "BANCO")
    validar_dataframe(df_erp, "ERP")

    df_banco = preparar_dataframe(df_banco)
    df_erp = preparar_dataframe(df_erp)

    df_resultado = resolver_candidatos_por_banco(
        matriz=matriz,
        df_banco=df_banco
    )

    df_resultado = resolver_conflictos_uno_a_uno(df_resultado)

    df_resultado = agregar_huerfanos_erp(
        df_resultado=df_resultado,
        df_erp=df_erp
    )

    return df_resultado[columnas_resultado()]


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def conciliar_con_matriz_scoring(
    df_banco,
    df_erp,
    devolver_matriz=False
):
    """
    Función principal del motor.

    Si devolver_matriz=False:
        devuelve df_resultado

    Si devolver_matriz=True:
        devuelve df_resultado, matriz
    """

    matriz = construir_matriz_scoring(
        df_banco=df_banco,
        df_erp=df_erp
    )

    df_resultado = resolver_conciliacion_desde_matriz(
        matriz=matriz,
        df_banco=df_banco,
        df_erp=df_erp
    )

    if devolver_matriz:
        return df_resultado, matriz

    return df_resultado
