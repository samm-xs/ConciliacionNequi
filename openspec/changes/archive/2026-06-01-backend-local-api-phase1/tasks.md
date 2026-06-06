# Tasks: Backend Local API Phase 1

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650-900 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 import/password/service seam → PR 2 FastAPI contract/deps/docs |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Import safety, Nequi password, service + CLI | PR 1 | Backend-only; include RED/GREEN tests and `python -m pytest -q`. |
| 2 | FastAPI API, dependency manifest, metadata/download contract | PR 2 | Depends on service seam; no frontend changes. |

## Phase 1: RED Tests for Service Boundary

- [x] 1.1 Create `tests/test_import_safety.py` asserting imports of `main`, `Backend.Extraccion.Extraccion_bancos.Nequi`, and service modules do not open PDFs, print tables, reconcile, or export Excel.
- [x] 1.2 Create `tests/test_nequi_password.py` asserting `extraer_movimientos_nequi(path, password)` forwards both provided password and `None` to `pdfplumber.open`.
- [x] 1.3 Create `tests/test_conciliacion_service.py` with monkeypatched pipeline functions verifying call order, password forwarding, explicit/default output path, and `ReconciliationResult` metadata.

## Phase 2: GREEN Service, Password, CLI

- [x] 2.1 Modify `Backend/Extraccion/Extraccion_bancos/Nequi.py` to accept `password=None`, remove hardcoded fallback, and guard demo/table printing from import.
- [x] 2.2 Create `Backend/Servicios/__init__.py` and `Backend/Servicios/conciliacion_service.py` with `ReconciliationResult` and `run_reconciliation(...)`, reusing existing business modules unchanged.
- [x] 2.3 Modify `main.py` into an argparse CLI guarded by `if __name__ == "__main__"`, delegating to `run_reconciliation`.
- [x] 2.4 Run targeted tests from Phase 1, then `python -m pytest -q`; fix only boundary regressions.

## Phase 3: RED/GREEN FastAPI Contract

- [x] 3.1 Create `tests/test_local_api.py` using FastAPI `TestClient` and fake service for successful multipart request, missing PDFs validation, password aliases, metadata, and service error response.
- [x] 3.2 Create `Backend/API/__init__.py` and `Backend/API/app.py` with FastAPI app factory, `POST /api/reconciliations`, temp uploaded PDFs, local output directory, and optional download URL.
- [x] 3.3 Add optional `GET /api/reconciliations/{filename}/download` in `Backend/API/app.py` if metadata includes `download_url`, preventing path traversal.

## Phase 4: Dependencies and Verification

- [x] 4.1 Create `requirements.txt` with existing libraries plus `fastapi`, `uvicorn`, `python-multipart`, `pytest`, and `httpx`.
- [x] 4.2 Verify no `Frontend/` files changed and no reconciliation/scoring/compound/Excel layout logic was rewritten.
- [x] 4.3 Run `python -m pytest -q` and ensure import safety, API contract, service orchestration, and existing 49 tests stay green.
