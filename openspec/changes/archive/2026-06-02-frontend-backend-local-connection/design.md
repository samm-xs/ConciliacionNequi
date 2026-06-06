# Design: Frontend Backend Local Connection

## Technical Approach

Add a thin local integration layer: FastAPI serves the existing static MVP page at `GET /`, and the existing inline frontend script submits both PDFs plus the optional bank password to same-origin `POST /api/reconciliations`. The backend reconciliation, Excel generation, and download contract stay unchanged; Phase 2 only connects the already-defined API contract to the static browser UI.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|----------|--------|-------------------------|-----------|
| Frontend serving | Return `Frontend/Diseño_mvp.html` from `Backend/API/app.py` using `FileResponse` | Mount the whole `Frontend/` directory; introduce a frontend dev server | A single route is the smallest local-only change and avoids CORS/build tooling. |
| File lookup | Resolve the HTML via `Path(__file__).resolve().parents[...] / "Frontend" / "Diseño_mvp.html"` | Depend on `Path.cwd()` | The filename contains `ñ`; a module-relative `Path` is safer across launch directories and Windows shells. |
| Browser request | `fetch('/api/reconciliations', { method: 'POST', body: formData })` | Absolute `http://127.0.0.1:8000/...`; CORS | Same-origin keeps the page portable under the local FastAPI host. |
| UI implementation | Extend existing inline JavaScript and markup | React/Vite or split JS assets | Scope requires minimal static HTML/JS and no toolchain. |

## Data Flow

```text
Browser GET / ──→ FastAPI / ──→ FileResponse Frontend/Diseño_mvp.html

User selects PDFs/password
  └─ submit button
      └─ FormData(erp_pdf, bank_pdf, password_banco)
          └─ fetch('/api/reconciliations')
              └─ existing runner/export flow
                  └─ JSON { download_url, metadata }
                      └─ UI ready state + download link
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `Backend/API/app.py` | Modify | Add `GET /` route inside `create_app()` that returns the existing HTML file. Preserve API and download routes. |
| `Frontend/Diseño_mvp.html` | Modify | Add password input, submit button, status/error region, download link, and inline JS state handling. |
| `tests/test_local_api.py` | Modify | Add pytest checks for `GET /`, static contract markers, and existing API/download behavior. |

## Interfaces / Contracts

Backend route:

```python
@app.get("/")
def frontend():
    return FileResponse(frontend_path)
```

Frontend `FormData` contract:

```javascript
formData.append('erp_pdf', erpFile);
formData.append('bank_pdf', bankFile);
formData.append('password_banco', bankPassword);
```

Successful API response MUST use the returned `download_url`; the frontend MUST NOT derive or hardcode workbook paths.

## UI State Model

| State | Trigger | UI behavior |
|-------|---------|-------------|
| Idle | Page load or reset | No error, no download, submit disabled until both PDFs exist. |
| Missing files | Submit without both PDFs | Show missing-file message; do not call the API. |
| Processing | Valid submit starts | Disable submit, show processing text, clear stale error/download. |
| Error | Non-2xx response, failed fetch, or missing `download_url` | Show clear error, keep submit retryable, hide download. |
| Ready | 2xx response with `download_url` | Show success text and download anchor using the API URL. |

## JavaScript Flow

1. `handleFile(input, displayId)` keeps current filename display behavior and calls `updateSubmitState()`.
2. `submitReconciliation()` reads `upload-libro`, `upload-extracto`, and password input values.
3. If either file is missing, set missing-file state and return.
4. Build `FormData` with `erp_pdf`, `bank_pdf`, `password_banco`.
5. `await fetch('/api/reconciliations', ...)`; parse JSON when available.
6. On API error, display `detail` or fallback message.
7. On success, require `download_url` and bind it to the download link.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit/static | Markup has password, submit, status/error/download seams and `fetch('/api/reconciliations')` | Pytest `GET /` response text assertions; no browser runner. |
| API contract | Multipart field names, password forwarding, validation error, service failure, `download_url` | Existing `TestClient` tests plus focused assertions. |
| E2E | Full browser interaction | Not added; out of scope for local MVP/toolchain constraints. |

Run instructions after implementation: from repo root, run `python -m pytest -q`, then start the app with the existing FastAPI entrypoint and open `http://127.0.0.1:8000/`.

## Migration / Rollout

No migration required. Rollback is limited to removing the `GET /` route, reverting `Frontend/Diseño_mvp.html`, and deleting Phase 2 pytest additions. Existing reconciliation and Excel output logic remain untouched.

## Open Questions

None.
