## Exploration: backend-local-api-phase1

### Current State
The current reconciliation flow is a script in `main.py` with hardcoded ERP and Nequi PDF paths. It imports extraction, normalization, reconciliation, compound detection, and Excel export functions, executes them immediately at module import/runtime, and writes the workbook through `exportar_resultado_conciliacion`.

The strongest backend seam is orchestration: keep the existing business modules intact and extract the `main.py` sequence into a callable service function that accepts local input paths and a bank PDF password. The biggest blocker is `Backend/Extraccion/Extraccion_bancos/Nequi.py`: it hardcodes `pdf_path`, hardcodes the password in `pdfplumber.open(..., password="18143115")`, and executes extraction/table printing at module level, so importing it can try to open a real local PDF before the caller provides inputs.

Existing tests use `pytest` and cover pure reconciliation engines, Nequi normalization, and Excel export behavior. No dependency manifest exists, but runtime imports indicate at least `pandas`, `pdfplumber`, `openpyxl`, and `tabulate` are needed. OpenSpec config requires strict TDD and `python -m pytest -q`.

### Affected Areas
- `main.py` — current hardcoded pipeline entry point; should become CLI/demo-only or delegate to a callable backend orchestration function without running on import.
- `Backend/Extraccion/Extraccion_bancos/Nequi.py` — must accept a password parameter and remove/guard module-level execution; this is required before any API can safely import the extractor.
- `Backend/Extraccion/Extraccion_ERP/Formato_vergel.py` — ERP extraction already accepts `pdf_path`; only needs import safety review because it still contains a hardcoded sample path variable and display/export helper code.
- `Backend/ExportacionExcel/Exportar_resultado_conciliacion.py` — already accepts `nombre_archivo`; backend service can pass an output path while preserving workbook layout.
- New backend boundary, suggested `Backend/Servicios/conciliacion_service.py` — orchestrates extract → normalize → separate bank concepts → reconcile → detect compounds → export Excel; returns metadata for API/CLI callers.
- New local API boundary, suggested `Backend/API/app.py` — thin local-only HTTP adapter for later frontend connection; should not contain reconciliation business logic.
- `tests/` — add strict TDD tests for orchestration, password forwarding, import safety, and endpoint contract using monkeypatched pipeline functions rather than real PDFs.

### Approaches
1. **Service-first seam with thin local API** — Introduce a callable reconciliation service and a minimal API adapter around it.
   - Pros: preserves business logic, isolates frontend-ready contract, makes tests fast with monkeypatching, keeps local-only scope clear.
   - Cons: requires a small new dependency if an HTTP framework is chosen; needs careful import cleanup in `Nequi.py` first.
   - Effort: Medium

2. **Patch `main.py` directly into an API handler** — Move request/file handling into the existing script flow.
   - Pros: fewest new files initially.
   - Cons: keeps orchestration coupled to transport, harder to test, easier to accidentally alter business logic or execute side effects on import.
   - Effort: Low initially, higher risk later

3. **Full backend package refactor** — Reorganize modules into a package with formal models, config, and layered architecture.
   - Pros: clean long-term structure.
   - Cons: too broad for Phase 1; risks changing reconciliation/scoring/Excel behavior.
   - Effort: High

### Recommendation
Use the service-first seam with a thin local API. Phase 1 should first make current modules import-safe, then extract the pipeline into a service function such as `run_reconciliation(erp_pdf_path, bank_pdf_path, bank_pdf_password, output_path=None) -> ReconciliationResult`. The API should be only an adapter that receives two local PDFs and `bank_pdf_password`, stores/copies them to a local working folder, calls the service, and returns Excel output metadata.

Suggested endpoint contract for the later frontend connection:

- `POST /api/reconciliations`
- Request: `multipart/form-data`
  - `erp_pdf`: required PDF file
  - `bank_pdf`: required PDF file
  - `bank_pdf_password`: required string
- Response `200`:
  - `status`: `completed`
  - `output_file`: generated `.xlsx` filename
  - `download_url`: local download route or file path for the generated workbook
  - optional counts: `erp_rows`, `bank_rows`, `reconciled_rows`, `compound_rows`
- Failure responses: validation errors for missing files/password and extraction errors for invalid password/unreadable PDFs.

Testing strategy under strict TDD:

- Add import-safety tests proving `main.py`/service/API imports do not open PDFs or print tables.
- Add a `Nequi.py` extractor test that monkeypatches `pdfplumber.open` and asserts the caller-supplied password is forwarded.
- Add service orchestration tests with monkeypatched extractor/normalizer/motor/export functions to verify call order, parameters, and output path without changing business logic.
- Add API contract tests with a local test client and monkeypatched service to verify multipart fields, password validation, and response shape.
- Keep existing `python -m pytest -q` green; do not require real PDFs in automated tests.

### Risks
- `Nequi.py` currently executes extraction and table printing at import time; any API/service import can fail before a request is handled.
- Bank PDF password is hardcoded today and must be parameterized without breaking existing extraction behavior.
- No dependency manifest exists; adding an API framework without pinning/documenting dependencies will make local setup fragile.
- Real PDF parsing is slow and file-specific; tests must use monkeypatches/fakes for service/API boundaries and avoid real PDFs.
- Excel formulas/layout are heavily tested; the backend should pass `nombre_archivo` but avoid changing workbook internals.

### Ready for Proposal
Yes — tell the user the minimal Phase 1 proposal should focus on import-safe backend modules, a service orchestration seam, password-parameterized Nequi extraction, a local-only upload endpoint contract, and pytest coverage before implementation. Do not include frontend implementation, authentication, database, cloud, or business-logic rewrites.
