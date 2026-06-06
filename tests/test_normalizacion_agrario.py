import pandas as pd
import pytest

from Backend.Normalizacion.Normalizacion_agrario.Normalizacion_extractoAgrario import (
    limpiar_nombre_agrario,
    normalizar_agrario,
    separar_conceptos_banco_agrario,
)


def test_normaliza_extracto_agrario_al_contrato_del_motor():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "descripcion": "Pago Proveedor Ñandú S.A.",
                "oficina": "INTERNET BANCA",
                "no_dcto": "12345",
                "valor": 152200.0,
                "saldo": 7416422.37,
            }
        ]
    )

    resultado = normalizar_agrario(df)

    assert list(resultado.columns) == ["id", "fecha", "nombre", "valor"]
    assert resultado.loc[0, "id"] == 1
    assert resultado.loc[0, "fecha"] == pd.Timestamp("2026-03-01")
    assert resultado.loc[0, "nombre"] == "a nandu pago proveedor s"
    assert resultado.loc[0, "valor"] == 152200.0


def test_limpia_tildes_mayusculas_signos_espacios_y_ordena_tokens():
    assert (
        limpiar_nombre_agrario("  TRANSFERENCIA   José-Pérez!!!  ")
        == "jose perez transferencia"
    )


def test_mantiene_valor_sin_modificar():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "descripcion": "Cliente Uno",
                "valor": "-4.152.508,00",
            }
        ]
    )

    resultado = normalizar_agrario(df)

    assert resultado.loc[0, "valor"] == "-4.152.508,00"


def test_valida_columnas_obligatorias():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "valor": 1000,
            }
        ]
    )

    with pytest.raises(ValueError, match="descripcion"):
        normalizar_agrario(df)


def test_descripcion_vacia_o_nan_devuelve_nombre_vacio():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "descripcion": None,
                "valor": 1000,
            },
            {
                "id": 2,
                "fecha": "2026-03-02",
                "descripcion": float("nan"),
                "valor": 2000,
            },
        ]
    )

    resultado = normalizar_agrario(df)

    assert list(resultado["nombre"]) == ["", ""]


def test_separa_conciliables_agrario_por_valor_positivo_y_resume_todo_el_extracto():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "fecha": "2026-03-01",
                "nombre": "consignacion credibanco d e",
                "valor": 1000,
            },
            {
                "id": 2,
                "fecha": "2026-03-01",
                "nombre": "a financiero gravamen movimiento",
                "valor": -40,
            },
            {
                "id": 3,
                "fecha": "2026-03-01",
                "nombre": "consignacion credibanco d e",
                "valor": 2000,
            },
            {
                "id": 4,
                "fecha": "2026-03-01",
                "nombre": "iva",
                "valor": 0,
            },
        ]
    )

    df_conciliable, df_resumen = separar_conceptos_banco_agrario(df)

    assert list(df_conciliable["id"]) == [1, 3]
    assert list(df_conciliable.columns) == ["id", "fecha", "nombre", "valor"]

    resumen = df_resumen.set_index("concepto")
    assert list(df_resumen.columns) == [
        "concepto",
        "cantidad movimientos",
        "valor total",
    ]
    assert resumen.loc["consignacion credibanco d e", "cantidad movimientos"] == 2
    assert resumen.loc["consignacion credibanco d e", "valor total"] == 3000
    assert resumen.loc["a financiero gravamen movimiento", "cantidad movimientos"] == 1
    assert resumen.loc["a financiero gravamen movimiento", "valor total"] == -40
    assert resumen.loc["iva", "cantidad movimientos"] == 1
    assert resumen.loc["iva", "valor total"] == 0


def test_separa_conceptos_agrario_valida_columnas_necesarias():
    df = pd.DataFrame([{"id": 1, "nombre": "consignacion"}])

    with pytest.raises(ValueError):
        separar_conceptos_banco_agrario(df)
