# Proposal: Backend Local API Phase 1

## Intent

Prepare the local MVP backend so a future frontend can submit two local PDFs plus the bank PDF password, run the existing reconciliation pipeline, and receive the generated Excel result without changing reconciliation, scoring, compound detection, or Excel layout behavior.

## Scope

### In Scope
- Make backend entry points import-safe by removing or guarding module-level PDF processing/printing.
- Add a callable reconciliation orchestration service accepting ERP PDF path, bank PDF path, bank PDF password, and optional Excel output path.
- Parameterize Nequi bank PDF extraction to use the caller-provided password.
- Add a thin local-only API contract for multipart PDF intake and Excel result metadata/download readiness.
- Add pytest coverage for import safety, password forwarding, service orchestration, and API contract using fakes/monkeypatches.

### Out of Scope
- Frontend implementation or UI integration.
- Authentication, authorization, database, cloud storage, deployment, or CI setup.
- Changes to reconciliation/scoring/compound business rules or Excel workbook layout.
- Real-PDF integration tests as a required automated test dependency.

## Capabilities

### New Capabilities
- `local-reconciliation-api`: Local backend contract for receiving two PDFs and a bank password, running reconciliation, and exposing Excel output metadata.
- `reconciliation-orchestration-service`: Import-safe callable boundary that coordinates existing extraction, normalization, reconciliation, compound detection, and Excel export modules.

### Modified Capabilities
- None — no existing main specs are present under `openspec/specs/`.

## Approach

Use the exploration-recommended service-first seam with a thin API adapter. First make `main.py` and bank extraction import-safe, then introduce `run_reconciliation(erp_pdf_path, bank_pdf_path, bank_pdf_password, output_path=None)`. The API only validates local multipart inputs, forwards parameters to the service, and returns completion/output metadata; business logic remains in existing modules.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `main.py` | Modified | Stop running hardcoded pipeline on import; delegate/demo only. |
| `Backend/Extraccion/Extraccion_bancos/Nequi.py` | Modified | Accept password parameter and remove import-time extraction side effects. |
| `Backend/Servicios/conciliacion_service.py` | New | Callable pipeline orchestration boundary. |
| `Backend/API/app.py` | New | Local-only HTTP adapter for future frontend connection. |
| `tests/` | Modified | Add TDD coverage without requiring real PDFs. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Import-time PDF execution breaks API startup | High | Add import-safety tests before refactor. |
| Password parameterization changes extraction behavior | Medium | Monkeypatch `pdfplumber.open` and assert password forwarding. |
| Excel output contract accidentally changes | Medium | Reuse exporter and keep existing Excel tests green. |
| API dependency/setup becomes fragile | Medium | Document/pin minimal local dependency if introduced. |

## Rollback Plan

Revert the new service/API files and restore the previous `main.py`/Nequi extraction entry behavior. Because business logic and Excel internals are out of scope, rollback should not require data/schema migration.

## Dependencies

- Existing runtime libraries: `pandas`, `pdfplumber`, `openpyxl`, `tabulate`.
- A minimal local Python HTTP framework may be selected during design/tasks.

## Success Criteria

- [ ] Backend accepts ERP PDF, bank PDF, and bank PDF password through a local-callable boundary.
- [ ] Generated Excel behavior/layout remains intact and existing tests stay green with `python -m pytest -q`.
- [ ] Imports of service/API do not open PDFs, print tables, or execute reconciliation.
- [ ] API contract is ready for future frontend connection without implementing frontend work.
