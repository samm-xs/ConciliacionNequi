# Proposal: Frontend Backend Local Connection

## Intent

Connect the existing static MVP frontend to the local FastAPI API so a user can open `http://127.0.0.1:8000/`, submit ERP/bank PDFs plus bank password, and download the generated Excel via the API `download_url`.

## Scope

### In Scope
- Serve `Frontend/Diseño_mvp.html` from FastAPI at `GET /`.
- Add static HTML controls/state for bank password, submit, API errors, processing, and download readiness.
- Submit multipart `FormData` to same-origin `POST /api/reconciliations` using existing fields.
- Use the response `download_url` for Excel download.
- Add pytest coverage for `/` serving and API/static contract expectations.

### Out of Scope
- React, Vite, new frontend tooling, browser E2E stack, or deployment work.
- Authentication, database, cloud storage, or production hardening.
- Reconciliation, scoring, compound detection, extraction, normalization, or Excel layout changes.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `local-reconciliation-api`: add local static frontend serving and browser submission/download expectations for the existing API contract.

## Approach

Use the minimal same-origin integration from exploration: add `GET /` in `Backend/API/app.py` returning the existing HTML by a `Path(__file__)`-relative lookup, then enhance `Frontend/Diseño_mvp.html` inline JavaScript to build `FormData`, call `/api/reconciliations`, render errors/status, and expose the returned `download_url`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `Backend/API/app.py` | Modified | Serve the static MVP HTML at `/` without changing API/download logic. |
| `Frontend/Diseño_mvp.html` | Modified | Add password, submit, request state, error, and download UI behavior. |
| `tests/test_local_api.py` | Modified | Cover frontend serving and preserve multipart/download contract. |
| `openspec/specs/local-reconciliation-api/spec.md` | Modified | Add Phase 2 frontend-serving and browser contract delta. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Non-ASCII HTML filename path resolution fails | Med | Resolve from backend file location, not process CWD. |
| Frontend shows stale download after failure | Med | Clear download state before each request and on errors. |
| Browser validation hides backend contract issues | Low | Keep pytest coverage for missing PDFs and API errors. |

## Rollback Plan

Remove the `GET /` route, revert `Frontend/Diseño_mvp.html` changes, and remove the added Phase 2 tests/spec delta. Existing `/api/reconciliations` and download endpoint behavior remains unchanged.

## Dependencies

- Existing FastAPI local app and pytest suite.
- No new frontend or runtime dependencies.

## Success Criteria

- [ ] `GET /` returns the existing MVP HTML.
- [ ] User can submit two PDFs plus optional bank password from the page.
- [ ] Successful API response exposes a working Excel download via `download_url`.
- [ ] API failures render a clear error without stale download links.
- [ ] `python -m pytest -q` remains green.
