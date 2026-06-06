from decimal import Decimal, InvalidOperation
from itertools import combinations
import re

import pandas as pd


TIPO_VARIOS_BANCO_A_UN_ERP = "varios_banco_a_un_erp"
TIPO_UN_BANCO_A_VARIOS_ERP = "un_banco_a_varios_erp"

ESTADO_COMPUESTO_DEFAULT = "Por revisar"
VALIDACION_COMPUESTO_OK = "OK"
ESTADOS_ERP_NO_DEFINITIVOS = ["huerfano_erp", "por_revisar", "ambiguo"]
VENTAJA_MINIMA_PRIORIDAD_NOMBRE = 2


COLUMNAS_REQUERIDAS = [
    "id_banco",
    "id_erp",
    "fecha_banco",
    "fecha_erp",
    "valor_banco",
    "valor_erp",
    "estado",
]


COLUMNAS_COMPUESTOS = [
    "tipo",
    "ids_banco",
    "ids_erp",
    "fecha_referencia",
    "valor_total_banco",
    "valor_total_erp",
    "diferencia",
    "cantidad_banco",
    "cantidad_erp",
    "estado_compuesto",
    "validacion_compuesto",
    "descripcion",
]


def validar_dataframe_resultado(df_resultado):
    faltantes = [
        columna for columna in COLUMNAS_REQUERIDAS
        if columna not in df_resultado.columns
    ]

    if faltantes:
        raise ValueError(
            "Al DataFrame de resultado le faltan columnas: "
            + ", ".join(faltantes)
        )


def normalizar_valor_contable(valor):
    if pd.isna(valor):
        return None

    if isinstance(valor, str) and valor.strip() == "":
        return None

    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def preparar_fecha(valor):
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return None

    return fecha


def clave_fecha(valor_fecha):
    fecha = preparar_fecha(valor_fecha)

    if fecha is None:
        return None

    return fecha.date()


def fechas_iguales(fecha_a, fecha_b):
    fecha_a = preparar_fecha(fecha_a)
    fecha_b = preparar_fecha(fecha_b)

    if fecha_a is None or fecha_b is None:
        return False

    return fecha_a.date() == fecha_b.date()


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


def calcular_prioridad_nombre(bancos, erps):
    tokens_bancos = [
        obtener_tokens_nombre(banco.get("nombre_banco"))
        for banco in bancos
    ]
    tokens_erps = [
        obtener_tokens_nombre(erp.get("nombre_erp"))
        for erp in erps
    ]

    tokens_bancos_union = set().union(*tokens_bancos) if tokens_bancos else set()
    tokens_erps_union = set().union(*tokens_erps) if tokens_erps else set()

    if len(tokens_bancos) > 1:
        tokens_comunes_banco = set.intersection(*tokens_bancos)
    else:
        tokens_comunes_banco = set()

    tokens_cruzados = tokens_bancos_union.intersection(tokens_erps_union)

    return len(tokens_comunes_banco) * 2 + len(tokens_cruzados)


def formatear_ids(registros, columna):
    ids = [
        str(int(registro[columna]))
        if isinstance(registro[columna], float) and registro[columna].is_integer()
        else str(registro[columna])
        for registro in registros
    ]

    return ", ".join(ids)


def suma_valores(registros, columna):
    total = Decimal("0")

    for registro in registros:
        valor = normalizar_valor_contable(registro[columna])

        if valor is None:
            return None

        total += valor

    return total


def agrupar_objetivos_por_valor(registros, columna_valor):
    objetivos = {}

    for registro in registros:
        valor = normalizar_valor_contable(registro[columna_valor])

        if valor is None:
            continue

        objetivos.setdefault(valor, []).append(registro)

    return objetivos


def buscar_combinaciones_con_objetivo(
    registros_compuestos,
    registros_objetivo,
    columna_valor_compuesto,
    columna_valor_objetivo,
    max_registros,
):
    objetivos_por_valor = agrupar_objetivos_por_valor(
        registros_objetivo,
        columna_valor_objetivo,
    )

    if not objetivos_por_valor:
        return []

    valores_objetivo = set(objetivos_por_valor)
    coincidencias = []

    for cantidad in range(2, max_registros + 1):
        for grupo in combinations(registros_compuestos, cantidad):
            valor_grupo = suma_valores(grupo, columna_valor_compuesto)

            if valor_grupo is None or valor_grupo not in valores_objetivo:
                continue

            objetivos = objetivos_por_valor[valor_grupo]

            if len(objetivos) != 1:
                continue

            coincidencias.append((list(grupo), objetivos[0], valor_grupo))

    return coincidencias


def resolver_coincidencias_por_prioridad_nombre(
    coincidencias,
    columna_id_objetivo,
    calcular_prioridad,
):
    coincidencias_por_objetivo = {}

    for coincidencia in coincidencias:
        id_objetivo = coincidencia[1][columna_id_objetivo]
        coincidencias_por_objetivo.setdefault(id_objetivo, []).append(coincidencia)

    coincidencias_resueltas = []

    for grupo_objetivo in coincidencias_por_objetivo.values():
        if len(grupo_objetivo) == 1:
            coincidencias_resueltas.append(grupo_objetivo[0])
            continue

        grupo_ordenado = sorted(
            (
                (calcular_prioridad(coincidencia), coincidencia)
                for coincidencia in grupo_objetivo
            ),
            key=lambda item: item[0],
            reverse=True,
        )

        mejor_prioridad, mejor_coincidencia = grupo_ordenado[0]
        segunda_prioridad = grupo_ordenado[1][0]

        if (
            mejor_prioridad > 0
            and mejor_prioridad - segunda_prioridad >= VENTAJA_MINIMA_PRIORIDAD_NOMBRE
        ):
            coincidencias_resueltas.append(mejor_coincidencia)

    return coincidencias_resueltas


def deduplicar_filas_compuestas(filas):
    filas_unicas = {}

    for prioridad, fila in filas:
        clave = (
            fila["tipo"],
            fila["ids_banco"],
            fila["ids_erp"],
        )

        if clave not in filas_unicas or prioridad > filas_unicas[clave][0]:
            filas_unicas[clave] = (prioridad, fila)

    return [
        fila
        for _, fila in sorted(
            filas_unicas.values(),
            key=lambda item: item[0],
            reverse=True,
        )
    ]


def construir_dataframe_vacio():
    return pd.DataFrame(columns=COLUMNAS_COMPUESTOS)


def obtener_bancos_candidatos(df_resultado):
    mascara = (
        df_resultado["id_banco"].notna()
        & ~df_resultado["estado"].eq("conciliado")
    )

    return df_resultado[mascara].copy()


def obtener_erp_candidatos(df_resultado):
    ids_erp_conciliados = set(
        df_resultado.loc[
            df_resultado["id_erp"].notna()
            & df_resultado["estado"].eq("conciliado"),
            "id_erp",
        ].tolist()
    )

    mascara = (
        df_resultado["id_erp"].notna()
        & df_resultado["estado"].isin(ESTADOS_ERP_NO_DEFINITIVOS)
        & ~df_resultado["id_erp"].isin(ids_erp_conciliados)
    )

    return (
        df_resultado[mascara]
        .drop_duplicates(subset=["id_erp"])
        .copy()
    )


def construir_fila_compuesto(
    tipo,
    bancos,
    erps,
    fecha_referencia,
    valor_total_banco,
    valor_total_erp,
    descripcion,
):
    diferencia = valor_total_banco - valor_total_erp

    return {
        "tipo": tipo,
        "ids_banco": formatear_ids(bancos, "id_banco"),
        "ids_erp": formatear_ids(erps, "id_erp"),
        "fecha_referencia": fecha_referencia.date()
        if hasattr(fecha_referencia, "date")
        else fecha_referencia,
        "valor_total_banco": valor_total_banco,
        "valor_total_erp": valor_total_erp,
        "diferencia": diferencia,
        "cantidad_banco": len(bancos),
        "cantidad_erp": len(erps),
        "estado_compuesto": ESTADO_COMPUESTO_DEFAULT,
        "validacion_compuesto": VALIDACION_COMPUESTO_OK
        if diferencia == Decimal("0")
        else "ERROR",
        "descripcion": descripcion,
    }


def detectar_varios_banco_a_un_erp(bancos_candidatos, erp_candidatos, max_registros):
    filas = []
    bancos = bancos_candidatos.to_dict("records")

    for _, erp in erp_candidatos.iterrows():
        erp_registro = erp.to_dict()
        bancos_misma_fecha = [
            banco for banco in bancos
            if fechas_iguales(banco["fecha_banco"], erp_registro["fecha_erp"])
        ]

        if len(bancos_misma_fecha) < 2:
            continue

        coincidencias = buscar_combinaciones_con_objetivo(
            registros_compuestos=bancos_misma_fecha,
            registros_objetivo=[erp_registro],
            columna_valor_compuesto="valor_banco",
            columna_valor_objetivo="valor_erp",
            max_registros=max_registros,
        )
        coincidencias = resolver_coincidencias_por_prioridad_nombre(
            coincidencias,
            "id_erp",
            lambda coincidencia: calcular_prioridad_nombre(
                coincidencia[0],
                [coincidencia[1]],
            ),
        )

        for grupo_bancos, erp_registro, valor_banco in coincidencias:
            fila = construir_fila_compuesto(
                    tipo=TIPO_VARIOS_BANCO_A_UN_ERP,
                    bancos=grupo_bancos,
                    erps=[erp_registro],
                    fecha_referencia=preparar_fecha(erp_registro["fecha_erp"]),
                    valor_total_banco=valor_banco,
                    valor_total_erp=normalizar_valor_contable(erp_registro["valor_erp"]),
                    descripcion=(
                        "Posible compuesto detectado por suma exacta "
                        "en la misma fecha. Revisar antes de conciliar."
                    ),
                )
            prioridad = calcular_prioridad_nombre(grupo_bancos, [erp_registro])
            filas.append((prioridad, fila))

    return filas


def detectar_un_banco_a_varios_erp(bancos_candidatos, erp_candidatos, max_registros):
    filas = []
    erps = erp_candidatos.to_dict("records")

    for _, banco in bancos_candidatos.iterrows():
        banco_registro = banco.to_dict()
        erps_misma_fecha = [
            erp for erp in erps
            if fechas_iguales(banco_registro["fecha_banco"], erp["fecha_erp"])
        ]

        if len(erps_misma_fecha) < 2:
            continue

        coincidencias = buscar_combinaciones_con_objetivo(
            registros_compuestos=erps_misma_fecha,
            registros_objetivo=[banco_registro],
            columna_valor_compuesto="valor_erp",
            columna_valor_objetivo="valor_banco",
            max_registros=max_registros,
        )
        coincidencias = resolver_coincidencias_por_prioridad_nombre(
            coincidencias,
            "id_banco",
            lambda coincidencia: calcular_prioridad_nombre(
                [coincidencia[1]],
                coincidencia[0],
            ),
        )

        for grupo_erps, banco_registro, valor_erp in coincidencias:
            fila = construir_fila_compuesto(
                    tipo=TIPO_UN_BANCO_A_VARIOS_ERP,
                    bancos=[banco_registro],
                    erps=grupo_erps,
                    fecha_referencia=preparar_fecha(banco_registro["fecha_banco"]),
                    valor_total_banco=normalizar_valor_contable(banco_registro["valor_banco"]),
                    valor_total_erp=valor_erp,
                    descripcion=(
                        "Posible compuesto detectado por suma exacta "
                        "en la misma fecha. Revisar antes de conciliar."
                    ),
                )
            prioridad = calcular_prioridad_nombre([banco_registro], grupo_erps)
            filas.append((prioridad, fila))

    return filas


def detectar_compuestos(df_resultado, max_registros=3):
    """
    Detecta posibles conciliaciones compuestas sobre registros pendientes.

    No modifica el resultado del motor uno-a-uno y nunca marca compuestos
    como conciliados automáticamente.
    """

    validar_dataframe_resultado(df_resultado)

    if max_registros < 2:
        raise ValueError("max_registros debe ser mayor o igual a 2.")

    bancos_candidatos = obtener_bancos_candidatos(df_resultado)
    erp_candidatos = obtener_erp_candidatos(df_resultado)

    if bancos_candidatos.empty or erp_candidatos.empty:
        return construir_dataframe_vacio()

    filas = []
    filas.extend(
        detectar_varios_banco_a_un_erp(
            bancos_candidatos=bancos_candidatos,
            erp_candidatos=erp_candidatos,
            max_registros=max_registros,
        )
    )
    filas.extend(
        detectar_un_banco_a_varios_erp(
            bancos_candidatos=bancos_candidatos,
            erp_candidatos=erp_candidatos,
            max_registros=max_registros,
        )
    )

    if not filas:
        return construir_dataframe_vacio()

    filas = deduplicar_filas_compuestas(filas)

    return pd.DataFrame(filas, columns=COLUMNAS_COMPUESTOS)
