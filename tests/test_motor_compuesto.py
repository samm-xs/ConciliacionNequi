import pandas as pd
import pytest

from Backend.MotorComparacion.Motor_compuesto import detectar_compuestos


def resultado(rows):
    columnas = [
        "id_banco",
        "id_erp",
        "fecha_banco",
        "fecha_erp",
        "nombre_banco",
        "nombre_erp",
        "valor_banco",
        "valor_erp",
        "estado",
    ]

    return pd.DataFrame(rows, columns=columnas)


def banco_pendiente(id_banco, fecha, valor, nombre=None):
    return {
        "id_banco": id_banco,
        "id_erp": None,
        "fecha_banco": fecha,
        "fecha_erp": None,
        "nombre_banco": nombre,
        "nombre_erp": None,
        "valor_banco": valor,
        "valor_erp": None,
        "estado": "huerfano_banco",
    }


def banco_con_pareja(id_banco, id_erp, fecha, valor, nombre_banco=None, nombre_erp=None):
    return {
        "id_banco": id_banco,
        "id_erp": id_erp,
        "fecha_banco": fecha,
        "fecha_erp": fecha,
        "nombre_banco": nombre_banco,
        "nombre_erp": nombre_erp,
        "valor_banco": valor,
        "valor_erp": valor,
        "estado": "por_revisar",
    }


def erp_pendiente(id_erp, fecha, valor, nombre=None):
    return {
        "id_banco": None,
        "id_erp": id_erp,
        "fecha_banco": None,
        "fecha_erp": fecha,
        "nombre_banco": None,
        "nombre_erp": nombre,
        "valor_banco": None,
        "valor_erp": valor,
        "estado": "huerfano_erp",
    }


def erp_no_pendiente(id_erp, fecha, valor, nombre=None):
    return {
        "id_banco": None,
        "id_erp": id_erp,
        "fecha_banco": None,
        "fecha_erp": fecha,
        "nombre_banco": None,
        "nombre_erp": nombre,
        "valor_banco": None,
        "valor_erp": valor,
        "estado": "por_revisar",
    }


def erp_ambiguo(id_erp, fecha, valor, nombre=None):
    return {
        "id_banco": None,
        "id_erp": id_erp,
        "fecha_banco": None,
        "fecha_erp": fecha,
        "nombre_banco": None,
        "nombre_erp": nombre,
        "valor_banco": None,
        "valor_erp": valor,
        "estado": "ambiguo",
    }


def test_detecta_varios_banco_a_un_erp():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_pendiente(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1

    fila = compuestos.iloc[0]

    assert fila["tipo"] == "varios_banco_a_un_erp"
    assert fila["ids_banco"] == "1, 2"
    assert fila["ids_erp"] == "10"
    assert fila["valor_total_banco"] == fila["valor_total_erp"]
    assert fila["diferencia"] == 0
    assert fila["cantidad_banco"] == 2
    assert fila["cantidad_erp"] == 1
    assert fila["estado_compuesto"] == "Por revisar"
    assert fila["validacion_compuesto"] == "OK"


def test_detecta_un_banco_a_varios_erp():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 50000),
        erp_pendiente(10, "2026-03-01", 20000),
        erp_pendiente(11, "2026-03-01", 30000),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1

    fila = compuestos.iloc[0]

    assert fila["tipo"] == "un_banco_a_varios_erp"
    assert fila["ids_banco"] == "1"
    assert fila["ids_erp"] == "10, 11"
    assert fila["valor_total_banco"] == fila["valor_total_erp"]
    assert fila["diferencia"] == 0
    assert fila["cantidad_banco"] == 1
    assert fila["cantidad_erp"] == 2
    assert fila["estado_compuesto"] == "Por revisar"
    assert fila["validacion_compuesto"] == "OK"


def test_no_detecta_si_la_suma_no_coincide():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_pendiente(10, "2026-03-01", 60000),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_no_usa_registros_ya_conciliados():
    df = resultado([
        {
            "id_banco": 1,
            "id_erp": 10,
            "fecha_banco": "2026-03-01",
            "fecha_erp": "2026-03-01",
            "nombre_banco": None,
            "nombre_erp": None,
            "valor_banco": 20000,
            "valor_erp": 20000,
            "estado": "conciliado",
        },
        banco_pendiente(2, "2026-03-01", 30000),
        erp_pendiente(20, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_usa_bancos_por_revisar_aunque_tengan_id_erp():
    df = resultado([
        banco_con_pareja(1, 99, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_pendiente(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_banco"] == "1, 2"


def test_usa_erp_por_revisar_si_no_esta_conciliado():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_no_pendiente(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_erp"] == "10"


def test_usa_erp_ambiguo_si_no_esta_conciliado():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_ambiguo(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_erp"] == "10"


def test_no_usa_erp_ya_conciliado():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        {
            "id_banco": 99,
            "id_erp": 10,
            "fecha_banco": "2026-03-01",
            "fecha_erp": "2026-03-01",
            "nombre_banco": None,
            "nombre_erp": None,
            "valor_banco": 50000,
            "valor_erp": 50000,
            "estado": "conciliado",
        },
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_respeta_maximo_de_tres_registros():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 10000),
        banco_pendiente(2, "2026-03-01", 10000),
        banco_pendiente(3, "2026-03-01", 10000),
        banco_pendiente(4, "2026-03-01", 10000),
        erp_pendiente(10, "2026-03-01", 40000),
    ])

    compuestos = detectar_compuestos(df, max_registros=3)

    assert compuestos.empty


def test_no_detecta_compuesto_con_desfase_de_un_dia():
    df = resultado([
        banco_pendiente(1, "2026-03-31", 20000),
        banco_pendiente(2, "2026-03-30", 30000),
        erp_pendiente(10, "2026-03-31", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_no_detecta_compuesto_con_desfase_mayor_a_dos_dias():
    df = resultado([
        banco_pendiente(1, "2026-03-31", 20000),
        banco_pendiente(2, "2026-03-28", 30000),
        erp_pendiente(10, "2026-03-31", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_nunca_devuelve_conciliado():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_pendiente(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert set(compuestos["estado_compuesto"]) == {"Por revisar"}
    assert "Conciliado" not in set(compuestos["estado_compuesto"])


def test_no_devuelve_compuesto_si_hay_multiples_combinaciones_para_el_mismo_objetivo():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 10000),
        banco_pendiente(2, "2026-03-01", 40000),
        banco_pendiente(3, "2026-03-01", 20000),
        banco_pendiente(4, "2026-03-01", 30000),
        erp_pendiente(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_resuelve_multiples_combinaciones_por_nombre_castro():
    df = resultado([
        banco_pendiente(785, "2026-03-14", 8000, "castro julian nefer"),
        banco_pendiente(786, "2026-03-14", 52500, "castro julian nefer"),
        banco_pendiente(770, "2026-03-14", 20000, "ricardo segundo"),
        banco_pendiente(771, "2026-03-14", 26200, "ingri la yajaira"),
        banco_pendiente(780, "2026-03-14", 14300, "andres benavides daniel"),
        erp_pendiente(530, "2026-03-14", 60500, "castro nefe palacio"),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_banco"] == "785, 786"
    assert compuestos.iloc[0]["ids_erp"] == "530"


def test_resuelve_multiples_combinaciones_por_nombre_emir_rosero():
    df = resultado([
        banco_pendiente(1300, "2026-03-02", 7400, "emir rosero yaqueline"),
        banco_pendiente(1302, "2026-03-02", 11600, "emir rosero yaqueline"),
        banco_pendiente(1266, "2026-03-02", 3500, "bancolombia desde qr recarga"),
        banco_pendiente(1294, "2026-03-02", 10000, "adalberto james"),
        banco_pendiente(1303, "2026-03-02", 5500, "daniel muriel nicolas"),
        erp_pendiente(84, "2026-03-02", 19000, "emir rosero toro yak"),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_banco"] == "1300, 1302"
    assert compuestos.iloc[0]["ids_erp"] == "84"


def test_resuelve_multiples_combinaciones_por_nombre_jeimy():
    df = resultado([
        banco_pendiente(683, "2026-03-16", 28000, "jeimy"),
        banco_pendiente(689, "2026-03-16", 6000, "amelia anghela ceron"),
        banco_pendiente(708, "2026-03-16", 6000, "jeimy"),
        banco_pendiente(712, "2026-03-16", 25200, "jeimy"),
        erp_pendiente(602, "2026-03-16", 59200, "jeimy riascos silva"),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_banco"] == "683, 708, 712"
    assert compuestos.iloc[0]["ids_erp"] == "602"


def test_no_resuelve_multiples_combinaciones_con_empate_de_nombre():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 10000, "cliente alfa"),
        banco_pendiente(2, "2026-03-01", 40000, "cliente beta"),
        banco_pendiente(3, "2026-03-01", 20000, "cliente gamma"),
        banco_pendiente(4, "2026-03-01", 30000, "cliente delta"),
        erp_pendiente(10, "2026-03-01", 50000, "cliente"),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_no_resuelve_multiples_combinaciones_con_ventaja_de_nombre_debil():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 10000, "cliente alfa"),
        banco_pendiente(2, "2026-03-01", 40000, "cliente beta"),
        banco_pendiente(3, "2026-03-01", 20000, "proveedor gamma"),
        banco_pendiente(4, "2026-03-01", 30000, "proveedor delta"),
        erp_pendiente(10, "2026-03-01", 50000, "cliente"),
    ])

    compuestos = detectar_compuestos(df)

    assert compuestos.empty


def test_evita_sugerencias_duplicadas_para_la_misma_combinacion():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        banco_pendiente(2, "2026-03-01", 30000),
        erp_pendiente(10, "2026-03-01", 50000),
        erp_ambiguo(10, "2026-03-01", 50000),
    ])

    compuestos = detectar_compuestos(df)

    assert len(compuestos) == 1
    assert compuestos.iloc[0]["ids_banco"] == "1, 2"
    assert compuestos.iloc[0]["ids_erp"] == "10"


def test_max_registros_debe_ser_mayor_o_igual_a_dos():
    df = resultado([
        banco_pendiente(1, "2026-03-01", 20000),
        erp_pendiente(10, "2026-03-03", 20000),
    ])

    with pytest.raises(ValueError):
        detectar_compuestos(df, max_registros=1)
