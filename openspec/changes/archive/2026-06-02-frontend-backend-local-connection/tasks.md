# Tasks: Frontend Backend Local Connection

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 180-280 |
| 900-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR: tests + FastAPI route + static HTML integration |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
900-line budget risk: Low
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Connect static MVP page to local FastAPI | PR 1 | Keep tests with route and HTML behavior; no business logic changes. |

## Phase 1: RED Tests / Contract Seams

- [x] 1.1 In `tests/test_local_api.py`, add failing pytest for `GET /` returning `Frontend/Diseño_mvp.html` and preserving `/api/reconciliations` availability.
- [x] 1.2 In `tests/test_local_api.py`, add failing static contract assertions for password input, submit/status/error/download seams, `fetch('/api/reconciliations')`, `FormData` fields, and `download_url` usage.
- [x] 1.3 In `tests/test_local_api.py`, keep or update API tests proving password forwarding, validation errors, service failures, and response `download_url` without real PDF parsing.

## Phase 2: GREEN Backend Serving

- [x] 2.1 In `Backend/API/app.py`, add a module-relative `Path` lookup for `Frontend/Diseño_mvp.html`, avoiding `Path.cwd()` and preserving non-ASCII filename handling.
- [x] 2.2 In `Backend/API/app.py`, add `GET /` inside `create_app()` returning `FileResponse(frontend_path)` without changing reconciliation or download routes.

## Phase 3: GREEN Static Frontend Integration

- [x] 3.1 In `Frontend/Diseño_mvp.html`, add bank password input plus submit, status/error, and download link elements using existing static markup patterns.
- [x] 3.2 In `Frontend/Diseño_mvp.html`, update inline JS so file selection calls `updateSubmitState()` and submit stays disabled until both PDFs exist.
- [x] 3.3 In `Frontend/Diseño_mvp.html`, implement `submitReconciliation()` to build `FormData` with `erp_pdf`, `bank_pdf`, `password_banco` and call same-origin `POST /api/reconciliations`.
- [x] 3.4 In `Frontend/Diseño_mvp.html`, handle missing-files, processing, API/fetch errors, missing `download_url`, and ready/download states while clearing stale downloads on retry/failure.

## Phase 4: Verification / Refactor

- [x] 4.1 Run `python -m pytest -q`; fix only regressions related to route serving or static contract expectations.
- [x] 4.2 Manually start the existing FastAPI entrypoint and open `http://127.0.0.1:8000/` to smoke-check page load and visible form states.
- [x] 4.3 Refactor duplicated test strings or JS helpers only if it improves clarity without adding frontend tooling.
