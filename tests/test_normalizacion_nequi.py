import pandas as pd
import pytest

from Backend.Normalizacion.Normalizacion_nequi.Normalizacion_extractoNequi import (
    limpiar_nombre_nequi,
    separar_conceptos_banco_nequi,
)


def test_separa_gravamen_e_intereses_del_dataframe_conciliable():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "nombre": "cliente uno",
                "valor": 10000,
            },
            {
                "id": 2,
                "fecha": "2026-03-01",
                "nombre": "al gravamen movimiento",
                "valor": -500,
            },
            {
                "id": 3,
                "fecha": "2026-03-01",
                "nombre": "de intereses pago",
                "valor": 25,
            },
        ]
    )

    df_conciliable, df_conceptos = separar_conceptos_banco_nequi(df)

    assert list(df_conciliable["id"]) == [1]
    assert set(df_conceptos["concepto"]) == {
        "al gravamen movimiento",
        "de intereses pago",
    }


def test_suma_conceptos_banco_por_concepto():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "nombre": "al gravamen movimiento",
                "valor": -500,
            },
            {
                "id": 2,
                "fecha": "2026-03-02",
                "nombre": "al gravamen movimiento",
                "valor": -700,
            },
            {
                "id": 3,
                "fecha": "2026-03-02",
                "nombre": "de intereses pago",
                "valor": 25,
            },
        ]
    )

    _, df_conceptos = separar_conceptos_banco_nequi(df)
    resumen = df_conceptos.set_index("concepto")

    assert resumen.loc["al gravamen movimiento", "cantidad movimientos"] == 2
    assert resumen.loc["al gravamen movimiento", "valor total"] == -1200
    assert resumen.loc["de intereses pago", "cantidad movimientos"] == 1
    assert resumen.loc["de intereses pago", "valor total"] == 25


def test_devuelve_conceptos_banco_vacio_con_columnas_esperadas():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "nombre": "cliente uno",
                "valor": 10000,
            },
        ]
    )

    df_conciliable, df_conceptos = separar_conceptos_banco_nequi(df)

    assert list(df_conciliable["id"]) == [1]
    assert df_conceptos.empty
    assert list(df_conceptos.columns) == [
        "concepto",
        "cantidad movimientos",
        "valor total",
    ]


def test_valida_columnas_necesarias_para_separar_conceptos_banco():
    df = pd.DataFrame([{"id": 1, "nombre": "cliente uno"}])

    with pytest.raises(ValueError):
        separar_conceptos_banco_nequi(df)


def test_limpia_recibi_por_y_de_sin_eliminar_bre_b():
    assert limpiar_nombre_nequi("RECIBI POR BRE-B DE: CLAUDIA") == "b bre claudia"
