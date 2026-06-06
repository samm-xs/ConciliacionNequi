import pandas as pd

from Backend.Servicios import conciliacion_service


def test_run_reconciliation_uses_explicit_output_and_preserves_pipeline_order(monkeypatch, tmp_path):
    events = []
    df_erp = pd.DataFrame([{"id": 1}])
    df_bank = pd.DataFrame([{"id": 2}])
    df_erp_normalizado = pd.DataFrame([{"id": 10, "fecha": "2026-03-01", "nombre": "erp", "valor": 100}])
    df_bank_normalizado = pd.DataFrame([{"id": 20, "fecha": "2026-03-01", "nombre": "bank", "valor": 100}])
    df_conceptos = pd.DataFrame([{"concepto": "gmf", "cantidad movimientos": 1, "valor total": -4}])
    df_resultado = pd.DataFrame([{"id_banco": 20, "id_erp": 10, "estado": "conciliado"}])
    df_compuestos = pd.DataFrame([{"ids_banco": "20", "ids_erp": "10"}])
    salida = tmp_path / "salida.xlsx"

    monkeypatch.setattr(
        conciliacion_service,
        "extraer_libro_auxiliar",
        lambda path: events.append(("extraer_erp", path)) or df_erp,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "extraer_movimientos_nequi",
        lambda path, password=None: events.append(("extraer_banco", path, password)) or df_bank,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_erp_nequi",
        lambda df: events.append(("normalizar_erp", len(df))) or df_erp_normalizado,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_nequi",
        lambda df: events.append(("normalizar_banco", len(df))) or df_bank_normalizado,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "separar_conceptos_banco_nequi",
        lambda df: events.append(("separar_conceptos", len(df))) or (df_bank_normalizado, df_conceptos),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "conciliar_con_matriz_scoring",
        lambda df_banco, df_erp, devolver_matriz=False: events.append(("conciliar", devolver_matriz)) or (df_resultado, "matriz"),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "detectar_compuestos",
        lambda df: events.append(("compuestos", len(df))) or df_compuestos,
    )
    def exportar_nequi(
        df_resultado_arg,
        df_compuestos_arg,
        nombre_archivo=None,
        df_conceptos_banco=None,
        df_banco_extraido=None,
        df_libro_auxiliar_extraido=None,
    ):
        events.append(
            (
                "exportar",
                nombre_archivo,
                df_conceptos_banco is df_conceptos,
                df_banco_extraido is df_bank,
                df_libro_auxiliar_extraido is df_erp,
            )
        )

    monkeypatch.setattr(
        conciliacion_service,
        "exportar_resultado_conciliacion",
        exportar_nequi,
    )

    resultado = conciliacion_service.run_reconciliation(
        "erp.pdf",
        "bank.pdf",
        bank_pdf_password="secreta",
        output_path=salida,
    )

    assert events == [
        ("extraer_erp", "erp.pdf"),
        ("extraer_banco", "bank.pdf", "secreta"),
        ("normalizar_erp", 1),
        ("normalizar_banco", 1),
        ("separar_conceptos", 1),
        ("conciliar", True),
        ("compuestos", 1),
        ("exportar", salida, True, True, True),
    ]
    assert resultado.status == "completed"
    assert resultado.output_path == salida
    assert resultado.output_file == "salida.xlsx"
    assert resultado.erp_rows == 1
    assert resultado.bank_rows == 1
    assert resultado.reconciled_rows == 1
    assert resultado.compound_rows == 1


def test_run_reconciliation_generates_default_output_path(monkeypatch, tmp_path):
    monkeypatch.setattr(
        conciliacion_service,
        "extraer_libro_auxiliar",
        lambda path: pd.DataFrame([{"id": 1}]),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "extraer_movimientos_nequi",
        lambda path, password=None: pd.DataFrame([{"id": 2}]),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_erp_nequi",
        lambda df: pd.DataFrame([{"id": 10, "fecha": "2026-03-01", "nombre": "erp", "valor": 100}]),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_nequi",
        lambda df: pd.DataFrame([{"id": 20, "fecha": "2026-03-01", "nombre": "bank", "valor": 100}]),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "separar_conceptos_banco_nequi",
        lambda df: (df, pd.DataFrame(columns=["concepto", "cantidad movimientos", "valor total"])),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "conciliar_con_matriz_scoring",
        lambda df_banco, df_erp, devolver_matriz=False: (pd.DataFrame([{"id_banco": 20, "id_erp": 10, "estado": "conciliado"}]), pd.DataFrame()),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "detectar_compuestos",
        lambda df: pd.DataFrame(),
    )

    exported = []
    monkeypatch.setattr(
        conciliacion_service,
        "exportar_resultado_conciliacion",
        lambda df_resultado_arg,
        df_compuestos_arg,
        nombre_archivo=None,
        df_conceptos_banco=None,
        df_banco_extraido=None,
        df_libro_auxiliar_extraido=None: exported.append(nombre_archivo),
    )
    monkeypatch.setattr(conciliacion_service.Path, "cwd", lambda: tmp_path)

    resultado = conciliacion_service.run_reconciliation("erp.pdf", "bank.pdf")

    assert len(exported) == 1
    assert exported[0] == resultado.output_path
    assert resultado.output_path.parent == tmp_path
    assert resultado.output_path.suffix == ".xlsx"
    assert resultado.output_file == resultado.output_path.name


def test_run_reconciliation_routes_agrario_to_agrario_extractor_and_normalizer(monkeypatch, tmp_path):
    events = []
    df_erp = pd.DataFrame([{"id": 1}])
    df_bank = pd.DataFrame([{"id": 2}])
    df_erp_normalizado = pd.DataFrame([{"id": 10, "fecha": "2026-03-01", "nombre": "erp", "valor": 100}])
    df_bank_normalizado = pd.DataFrame(
        [
            {"id": 20, "fecha": "2026-03-01", "nombre": "agrario positivo", "valor": 100},
            {"id": 21, "fecha": "2026-03-01", "nombre": "agrario negativo", "valor": -10},
        ]
    )
    df_bank_conciliable = df_bank_normalizado[df_bank_normalizado["valor"] > 0].copy()
    df_conceptos_agrario = pd.DataFrame(
        [
            {
                "concepto": "agrario positivo",
                "cantidad movimientos": 1,
                "valor total": 100,
            },
            {
                "concepto": "agrario negativo",
                "cantidad movimientos": 1,
                "valor total": -10,
            },
        ]
    )
    df_resultado = pd.DataFrame([{"id_banco": 20, "id_erp": 10, "estado": "conciliado"}])
    df_compuestos = pd.DataFrame()
    salida = tmp_path / "agrario.xlsx"

    monkeypatch.setattr(
        conciliacion_service,
        "extraer_libro_auxiliar",
        lambda path: events.append(("extraer_erp", path)) or df_erp,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "extraer_movimientos_nequi",
        lambda path, password=None: events.append(("extraer_nequi", path, password)) or pd.DataFrame(),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "extraer_extracto_agrario",
        lambda path: events.append(("extraer_agrario", path)) or df_bank,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_erp_nequi",
        lambda df: events.append(("normalizar_erp", len(df))) or df_erp_normalizado,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_nequi",
        lambda df: events.append(("normalizar_nequi", len(df))) or pd.DataFrame(),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "normalizar_agrario",
        lambda df: events.append(("normalizar_agrario", len(df))) or df_bank_normalizado,
    )
    monkeypatch.setattr(
        conciliacion_service,
        "separar_conceptos_banco_nequi",
        lambda df: events.append(("separar_conceptos", len(df))) or (df, pd.DataFrame()),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "separar_conceptos_banco_agrario",
        lambda df: events.append(("separar_conceptos_agrario", len(df))) or (df_bank_conciliable, df_conceptos_agrario),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "conciliar_con_matriz_scoring",
        lambda df_banco, df_erp, devolver_matriz=False: events.append(("conciliar", len(df_banco), len(df_erp))) or (df_resultado, "matriz"),
    )
    monkeypatch.setattr(
        conciliacion_service,
        "detectar_compuestos",
        lambda df: events.append(("compuestos", len(df))) or df_compuestos,
    )
    def exportar_agrario(
        df_resultado_arg,
        df_compuestos_arg,
        nombre_archivo=None,
        df_conceptos_banco=None,
        df_banco_extraido=None,
        df_libro_auxiliar_extraido=None,
    ):
        events.append(
            (
                "exportar",
                nombre_archivo,
                df_conceptos_banco is df_conceptos_agrario,
                df_banco_extraido is df_bank,
                df_libro_auxiliar_extraido is df_erp,
            )
        )

    monkeypatch.setattr(
        conciliacion_service,
        "exportar_resultado_conciliacion",
        exportar_agrario,
    )

    resultado = conciliacion_service.run_reconciliation(
        "erp.pdf",
        "agrario.pdf",
        bank_pdf_password="no-debe-usarse",
        output_path=salida,
        bank_type="agrario",
    )

    assert events == [
        ("extraer_erp", "erp.pdf"),
        ("extraer_agrario", "agrario.pdf"),
        ("normalizar_erp", 1),
        ("normalizar_agrario", 1),
        ("separar_conceptos_agrario", 2),
        ("conciliar", 1, 1),
        ("compuestos", 1),
        ("exportar", salida, True, True, True),
    ]
    assert resultado.bank_rows == 1
    assert resultado.output_file == "agrario.xlsx"


def test_run_reconciliation_rejects_unsupported_bank_type(tmp_path):
    try:
        conciliacion_service.run_reconciliation(
            "erp.pdf",
            "bank.pdf",
            output_path=tmp_path / "resultado.xlsx",
            bank_type="otro",
        )
    except ValueError as exc:
        assert "Unsupported bank_type" in str(exc)
    else:
        raise AssertionError("Expected unsupported bank_type to raise ValueError")
