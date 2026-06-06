import pandas as pd

from Backend.MotorComparacion.Motor_conciliacion import (
    conciliar_con_matriz_scoring,
)


def banco(rows):
    return pd.DataFrame(rows)


def erp(rows):
    return pd.DataFrame(rows)


def fila_banco(resultado, id_banco):
    encontrada = resultado[resultado["id_banco"].eq(id_banco)]
    assert len(encontrada) == 1
    return encontrada.iloc[0]


def filas_erp_huerfanas(resultado):
    return resultado[resultado["estado"].eq("huerfano_erp")]


def test_valor_distinto_no_genera_candidato_aunque_fecha_y_nombre_coincidan():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 1000.00},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 1000.01},
    ])

    resultado, matriz = conciliar_con_matriz_scoring(
        df_banco,
        df_erp,
        devolver_matriz=True,
    )

    assert matriz.empty
    assert fila_banco(resultado, 1)["estado"] == "huerfano_banco"
    assert set(filas_erp_huerfanas(resultado)["id_erp"]) == {10}


def test_valor_y_fecha_exactos_con_unico_candidato_concilian_automaticamente():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "alfa banco", "valor": 5000},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "beta erp", "valor": 5000},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    fila = fila_banco(resultado, 1)
    assert fila["estado"] == "conciliado"
    assert fila["id_erp"] == 10
    assert fila["score_fecha"] == 70
    assert fila["score_nombre"] == 0
    assert fila["score_total"] == 70


def test_varios_candidatos_con_mismo_valor_y_fecha_usan_tokens_para_desempatar():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 7000},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "maria lopez", "valor": 7000},
        {"id": 20, "fecha": "2026-03-01", "nombre": "ceron", "valor": 7000},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    fila = fila_banco(resultado, 1)
    assert fila["estado"] == "conciliado"
    assert fila["id_erp"] == 20
    assert fila["score_fecha"] == 70
    assert fila["score_nombre"] == 10
    assert fila["score_total"] == 80
    assert set(filas_erp_huerfanas(resultado)["id_erp"]) == {10}


def test_empate_real_despues_de_fecha_y_tokens_queda_ambiguo():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 7000},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "jose", "valor": 7000},
        {"id": 20, "fecha": "2026-03-01", "nombre": "ceron", "valor": 7000},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    fila = fila_banco(resultado, 1)
    assert fila["estado"] == "ambiguo"
    assert pd.isna(fila["id_erp"])
    assert "10" in fila["observacion"]
    assert "20" in fila["observacion"]
    assert set(filas_erp_huerfanas(resultado)["id_erp"]) == {10, 20}


def test_valor_exacto_fecha_distinta_y_token_de_nombre_queda_por_revisar():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 9000},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-02", "nombre": "ceron", "valor": 9000},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    fila = fila_banco(resultado, 1)
    assert fila["estado"] == "por_revisar"
    assert fila["id_erp"] == 10
    assert fila["score_fecha"] == 0
    assert fila["score_nombre"] == 10
    assert fila["score_total"] == 10


def test_erp_no_usado_queda_huerfano_erp():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "uno", "valor": 100},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "otro", "valor": 100},
        {"id": 20, "fecha": "2026-03-01", "nombre": "sobrante", "valor": 200},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    assert fila_banco(resultado, 1)["estado"] == "conciliado"
    assert set(filas_erp_huerfanas(resultado)["id_erp"]) == {20}


def test_banco_sin_valor_coincidente_queda_huerfano_banco():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 300},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 400},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    assert fila_banco(resultado, 1)["estado"] == "huerfano_banco"


def test_no_existe_tolerancia_entre_valores_contables():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": "1000.00"},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": "1000.01"},
    ])

    resultado, matriz = conciliar_con_matriz_scoring(
        df_banco,
        df_erp,
        devolver_matriz=True,
    )

    assert matriz.empty
    assert fila_banco(resultado, 1)["estado"] == "huerfano_banco"


def test_conflicto_uno_a_uno_se_resuelve_por_mayor_score():
    df_banco = banco([
        {"id": 1, "fecha": "2026-03-01", "nombre": "jose ceron", "valor": 8000},
        {"id": 2, "fecha": "2026-03-02", "nombre": "sin pista", "valor": 8000},
    ])
    df_erp = erp([
        {"id": 10, "fecha": "2026-03-01", "nombre": "ceron", "valor": 8000},
    ])

    resultado = conciliar_con_matriz_scoring(df_banco, df_erp)

    ganador = fila_banco(resultado, 1)
    perdedor = fila_banco(resultado, 2)

    assert ganador["estado"] == "conciliado"
    assert ganador["id_erp"] == 10
    assert perdedor["estado"] == "huerfano_banco"
    assert pd.isna(perdedor["id_erp"])
