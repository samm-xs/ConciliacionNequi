from pathlib import Path

from fastapi.testclient import TestClient

from Backend.API.app import create_app
from Backend.Servicios.conciliacion_service import ReconciliationResult


FRONTEND_HTML_PATH = Path(__file__).resolve().parents[1] / "Frontend" / "Diseño_mvp.html"


def pdf_file(name):
    return (name, b"%PDF-1.4 fake", "application/pdf")


def test_root_serves_existing_frontend_html_and_keeps_api_available(tmp_path):
    app = create_app(output_dir=tmp_path, reconciliation_runner=lambda *args, **kwargs: None)
    client = TestClient(app)

    root_response = client.get("/")
    api_response = client.post(
        "/api/reconciliations",
        files={"erp_pdf": pdf_file("erp.pdf")},
    )

    assert root_response.status_code == 200
    assert root_response.headers["content-type"].startswith("text/html")
    assert root_response.text.replace("\r\n", "\n") == FRONTEND_HTML_PATH.read_text(encoding="utf-8")
    assert api_response.status_code == 422


def test_root_html_exposes_static_frontend_contract_seams(tmp_path):
    app = create_app(output_dir=tmp_path, reconciliation_runner=lambda *args, **kwargs: None)
    client = TestClient(app)

    response = client.get("/")
    html = response.text

    assert response.status_code == 200
    assert 'id="bank-password"' in html
    assert 'id="bank-type"' in html
    assert 'value="nequi"' in html
    assert 'value="agrario"' in html
    assert 'type="password"' in html
    assert 'id="submit-reconciliation"' in html
    assert 'id="status-message"' in html
    assert 'id="error-message"' in html
    assert 'id="download-link"' in html
    assert "fetch('/api/reconciliations'" in html
    assert "formData.append('erp_pdf'" in html
    assert "formData.append('bank_pdf'" in html
    assert "formData.append('bank_type'" in html
    assert "formData.append('password_banco'" in html
    assert "download_url" in html
    assert "updateSubmitState()" in html


def test_post_reconciliation_returns_metadata_and_forwards_primary_password_field(tmp_path):
    calls = []

    def fake_service(erp_pdf_path, bank_pdf_path, bank_pdf_password=None, output_path=None, bank_type="nequi"):
        calls.append((Path(erp_pdf_path).name, Path(bank_pdf_path).name, bank_pdf_password, output_path, bank_type))
        return ReconciliationResult(
            status="completed",
            output_path=tmp_path / "resultado.xlsx",
            output_file="resultado.xlsx",
            erp_rows=3,
            bank_rows=4,
            reconciled_rows=2,
            compound_rows=1,
        )

    app = create_app(output_dir=tmp_path, reconciliation_runner=fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/reconciliations",
        files={"erp_pdf": pdf_file("erp.pdf"), "bank_pdf": pdf_file("bank.pdf")},
        data={"bank_pdf_password": "secreta", "bank_type": "agrario"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "output_file": "resultado.xlsx",
        "output_path": str(tmp_path / "resultado.xlsx"),
        "download_url": "/api/reconciliations/resultado.xlsx/download",
        "erp_rows": 3,
        "bank_rows": 4,
        "reconciled_rows": 2,
        "compound_rows": 1,
    }
    assert len(calls) == 1
    assert calls[0][0] == "erp.pdf"
    assert calls[0][1] == "bank.pdf"
    assert calls[0][2] == "secreta"
    assert calls[0][3] == tmp_path / "resultado.xlsx"
    assert calls[0][4] == "agrario"


def test_post_reconciliation_accepts_password_banco_alias(tmp_path):
    calls = []

    def fake_service(erp_pdf_path, bank_pdf_path, bank_pdf_password=None, output_path=None, bank_type="nequi"):
        calls.append(bank_pdf_password)
        return ReconciliationResult(
            status="completed",
            output_path=tmp_path / "resultado.xlsx",
            output_file="resultado.xlsx",
        )

    app = create_app(output_dir=tmp_path, reconciliation_runner=fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/reconciliations",
        files={"erp_pdf": pdf_file("erp.pdf"), "bank_pdf": pdf_file("bank.pdf")},
        data={"password_banco": "alias"},
    )

    assert response.status_code == 200
    assert calls == ["alias"]


def test_post_reconciliation_defaults_bank_type_to_nequi(tmp_path):
    calls = []

    def fake_service(erp_pdf_path, bank_pdf_path, bank_pdf_password=None, output_path=None, bank_type="nequi"):
        calls.append(bank_type)
        return ReconciliationResult(
            status="completed",
            output_path=tmp_path / "resultado.xlsx",
            output_file="resultado.xlsx",
        )

    app = create_app(output_dir=tmp_path, reconciliation_runner=fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/reconciliations",
        files={"erp_pdf": pdf_file("erp.pdf"), "bank_pdf": pdf_file("bank.pdf")},
    )

    assert response.status_code == 200
    assert calls == ["nequi"]


def test_post_reconciliation_validation_error_when_missing_pdf(tmp_path):
    called = False

    def fake_service(*args, **kwargs):
        nonlocal called
        called = True

    app = create_app(output_dir=tmp_path, reconciliation_runner=fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/reconciliations",
        files={"erp_pdf": pdf_file("erp.pdf")},
    )

    assert response.status_code == 422
    assert called is False


def test_post_reconciliation_returns_error_payload_when_service_fails(tmp_path):
    def fake_service(*args, **kwargs):
        raise RuntimeError("boom")

    app = create_app(output_dir=tmp_path, reconciliation_runner=fake_service)
    client = TestClient(app)

    response = client.post(
        "/api/reconciliations",
        files={"erp_pdf": pdf_file("erp.pdf"), "bank_pdf": pdf_file("bank.pdf")},
    )

    assert response.status_code == 500
    assert response.json() == {"status": "error", "detail": "boom"}


def test_download_endpoint_serves_only_files_inside_output_directory(tmp_path):
    workbook = tmp_path / "resultado.xlsx"
    workbook.write_bytes(b"excel")

    app = create_app(output_dir=tmp_path, reconciliation_runner=lambda *args, **kwargs: None)
    client = TestClient(app)

    ok_response = client.get("/api/reconciliations/resultado.xlsx/download")
    blocked_response = client.get("/api/reconciliations/..%2Fsecreto.xlsx/download")

    assert ok_response.status_code == 200
    assert ok_response.content == b"excel"
    assert blocked_response.status_code == 404
