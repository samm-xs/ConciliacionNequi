import builtins
import importlib
import sys


MODULES_UNDER_TEST = [
    "main",
    "Backend.Extraccion.Extraccion_bancos.Agrario",
    "Backend.Extraccion.Extraccion_bancos.Nequi",
    "Backend.Servicios.conciliacion_service",
]


def import_fresh(module_name):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_imports_do_not_open_pdfs_print_or_execute_pipeline(monkeypatch):
    events = []

    def fail_pdf_open(*args, **kwargs):
        events.append(("pdf_open", args, kwargs))
        raise AssertionError("pdfplumber.open must not run during import")

    def fail_print(*args, **kwargs):
        events.append(("print", args, kwargs))
        raise AssertionError("print must not run during import")

    def fail_export(*args, **kwargs):
        events.append(("export", args, kwargs))
        raise AssertionError("Excel export must not run during import")

    def fail_reconcile(*args, **kwargs):
        events.append(("reconcile", args, kwargs))
        raise AssertionError("reconciliation must not run during import")

    monkeypatch.setattr("pdfplumber.open", fail_pdf_open)
    monkeypatch.setattr(builtins, "print", fail_print)
    monkeypatch.setattr(
        "Backend.ExportacionExcel.Exportar_resultado_conciliacion.exportar_resultado_conciliacion",
        fail_export,
    )
    monkeypatch.setattr(
        "Backend.MotorComparacion.Motor_conciliacion.conciliar_con_matriz_scoring",
        fail_reconcile,
    )

    imported_modules = [import_fresh(module_name) for module_name in MODULES_UNDER_TEST]

    assert [module.__name__ for module in imported_modules] == MODULES_UNDER_TEST
    assert events == []


def test_agrario_does_not_expose_hardcoded_pdf_path():
    agrario = import_fresh("Backend.Extraccion.Extraccion_bancos.Agrario")

    assert not hasattr(agrario, "pdf_path")
    assert callable(agrario.extraer_extracto_agrario)
