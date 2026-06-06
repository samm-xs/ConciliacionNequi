from types import SimpleNamespace

import pandas as pd

from Backend.Extraccion.Extraccion_bancos.Nequi import extraer_movimientos_nequi


def build_pdf():
    table = [
        ["Fecha del movimiento", "Descripción", "Valor", "Saldo"],
        ["01/03/2026", "Pago recibido", "$1,000.00", "$5,000.00"],
    ]
    page = SimpleNamespace(extract_tables=lambda: [table])

    class FakePdf:
        pages = [page]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    return FakePdf()


def test_extraer_movimientos_nequi_forward_password(monkeypatch):
    calls = []

    def fake_open(path, password=None):
        calls.append((path, password))
        return build_pdf()

    monkeypatch.setattr("pdfplumber.open", fake_open)

    resultado = extraer_movimientos_nequi("nequi.pdf", password="clave-secreta")

    assert calls == [("nequi.pdf", "clave-secreta")]
    assert list(resultado.columns) == ["id", "Fecha del movimiento", "Descripción", "Valor", "Saldo"]
    assert resultado.loc[0, "Valor"] == 1000.0


def test_extraer_movimientos_nequi_forward_none_password(monkeypatch):
    calls = []

    def fake_open(path, password=None):
        calls.append((path, password))
        return build_pdf()

    monkeypatch.setattr("pdfplumber.open", fake_open)

    resultado = extraer_movimientos_nequi("nequi.pdf")

    assert calls == [("nequi.pdf", None)]
    assert pd.isna(resultado.loc[0, "Fecha del movimiento"]) is False
