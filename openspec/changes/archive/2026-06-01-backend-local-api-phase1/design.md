# Design: Backend Local API Phase 1

## Technical Approach

Create an import-safe service seam around the current `main.py` pipeline, then expose it through a thin local FastAPI adapter and an explicit CLI. Existing extraction, normalization, scoring, compound detection, and Excel export modules remain the source of business behavior; this change only moves orchestration and input/output boundaries. This satisfies `reconciliation-orchestration-service` and `local-reconciliation-api` specs without frontend work.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| API runtime | FastAPI app in `Backend/API/app.py` | Stdlib HTTP server, direct CLI-only boundary | FastAPI is the agreed adapter and gives explicit request contracts, upload handling, OpenAPI docs, and a pytest-compatible test client; `python-multipart` is required for multipart PDF uploads. |
| Orchestration seam | `Backend/Servicios/conciliacion_service.py` with `run_reconciliation(...) -> ReconciliationResult` | Put logic in `main.py` or API handler | Keeps transport, CLI, and business pipeline separated and easy to monkeypatch. |
| Password handling | `bank_pdf_password: str | None = None` forwarded to `extraer_movimientos_nequi(pdf_path, password=None)` | Hardcoded fallback or required-only password | Specs require explicit optional password and no hardcoded fallback. |
| File handling | Per-request `TemporaryDirectory` for uploaded PDFs; persistent local output dir for `.xlsx` | Keep uploads beside output, in-memory only | Temporary inputs are cleaned after service returns; output must survive for metadata/download readiness. |
| CLI migration | `main.py` becomes argparse entry point guarded by `if __name__ == "__main__"` | Delete script, keep hardcoded demo | Preserves a local manual path while preventing import-time PDF execution. |

## Data Flow

```text
HTTP multipart / CLI args
  -> local file paths
  -> run_reconciliation
  -> extract ERP + extract Nequi(password)
  -> normalize ERP/Nequi -> separate bank concepts
  -> conciliar_con_matriz_scoring -> detectar_compuestos
  -> exportar_resultado_conciliacion(output_path)
  -> ReconciliationResult metadata
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `Backend/Servicios/__init__.py` | Create | Marks service package. |
| `Backend/Servicios/conciliacion_service.py` | Create | Defines `ReconciliationResult` and `run_reconciliation`. Generates default `.xlsx` path when omitted. |
| `Backend/API/__init__.py` | Create | Marks API package. |
| `Backend/API/app.py` | Create | FastAPI app factory, `POST /api/reconciliations`, optional `GET /api/reconciliations/{filename}/download`. |
| `Backend/Extraccion/Extraccion_bancos/Nequi.py` | Modify | Add `password=None`; pass to `pdfplumber.open`; move demo/table printing behind explicit function or main guard. |
| `main.py` | Modify | Replace module-level execution with argparse CLI delegating to service. |
| `requirements.txt` | Create | Include existing runtime libs plus `fastapi`, `uvicorn`, `python-multipart`, `pytest`, and `httpx` for the FastAPI test client. |
| `tests/test_import_safety.py` | Create | Verifies imports do not open PDFs, export Excel, or print tables. |
| `tests/test_nequi_password.py` | Create | Verifies caller password, including `None`, reaches `pdfplumber.open`. |
| `tests/test_conciliacion_service.py` | Create | Monkeypatches pipeline functions and verifies order, params, output path, metadata. |
| `tests/test_local_api.py` | Create | FastAPI `TestClient` contract tests for valid/missing multipart fields and service errors. |

## Interfaces / Contracts

```python
@dataclass(frozen=True)
class ReconciliationResult:
    status: str
    output_path: Path
    output_file: str
    erp_rows: int | None = None
    bank_rows: int | None = None
    reconciled_rows: int | None = None
    compound_rows: int | None = None

def run_reconciliation(
    erp_pdf_path: str | Path,
    bank_pdf_path: str | Path,
    bank_pdf_password: str | None = None,
    output_path: str | Path | None = None,
) -> ReconciliationResult: ...
```

API: `POST /api/reconciliations` multipart fields `erp_pdf: UploadFile`, `bank_pdf: UploadFile`, optional `bank_pdf_password: Form(None)` and accepted alias `password_banco`. Success `200` returns `status`, `output_file`, `output_path`, optional `download_url`, and counts. Request validation returns FastAPI validation errors for missing PDFs; service/extraction failures return `500` with `status: "error"`.

CLI: `python main.py --erp-pdf <path> --bank-pdf <path> [--bank-pdf-password <password>] [--output <xlsx>]`.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Import safety, Nequi password forwarding, service call order | pytest monkeypatches/fakes; no real PDFs. |
| Integration | API request/response contract | FastAPI `TestClient` with monkeypatched service. |
| E2E | Existing pipeline behavior | Keep existing pytest suite green; real-PDF E2E remains manual/out of scope. |

## Migration / Rollout

No data migration required. Roll out by first adding failing tests, then import-safety refactors, then service, CLI, API, and dependency manifest. Existing Excel exporter remains unchanged except being called with `nombre_archivo`.

## Open Questions

- [ ] Confirm whether the public password field should be standardized as `bank_pdf_password` or Spanish `password_banco`; design accepts both for Phase 1 compatibility.
