## Exploration: frontend-backend-local-connection

### Current State
Backend Phase 1 exposes a local FastAPI app in `Backend/API/app.py` with `create_app(output_dir=None, reconciliation_runner=run_reconciliation)`. The existing API accepts `POST /api/reconciliations` multipart fields `erp_pdf`, `bank_pdf`, and optional `bank_pdf_password` or `password_banco`, writes uploaded PDFs to a temporary directory, runs the reconciliation service, and returns metadata including `download_url`. It also exposes `GET /api/reconciliations/{filename}/download` and protects downloads from path traversal.

The frontend is a static Tailwind HTML file at `Frontend/Diseño_mvp.html`. Today it only lets the user select/display two PDF filenames through inline JavaScript; it does not have a bank password input, submit action, API call, status state, error rendering, or download behavior. FastAPI does not yet serve the frontend at `/`.

Existing tests are pytest-based. `tests/test_local_api.py` already covers the multipart API contract, password alias forwarding, failure payload, and download endpoint. No browser/E2E runner exists, so Phase 2 should add focused API/static-file contract tests and keep frontend JavaScript simple enough to validate by DOM/markup assertions where practical.

### Affected Areas
- `Backend/API/app.py` — add the `/` route that serves `Frontend/Diseño_mvp.html` without changing reconciliation business logic, and keep existing API/download behavior intact.
- `Frontend/Diseño_mvp.html` — add password input, submit/download controls, and minimal client-side JavaScript for `FormData`, processing/error/ready states, and `download_url` handling while preserving the current visual design.
- `tests/test_local_api.py` — extend FastAPI `TestClient` coverage for serving the frontend from `/` and preserving the API contract.
- `tests/` — optionally add lightweight frontend markup/static behavior checks if they can remain dependency-free; no Playwright/Vite/browser stack should be introduced for this local MVP.
- `openspec/specs/local-reconciliation-api/spec.md` — likely needs a Phase 2 delta describing local frontend serving and browser submission expectations.

### Approaches
1. **Minimal static HTML served by FastAPI** — Add a `GET /` `FileResponse` for the existing HTML and enhance inline JavaScript to submit to the same-origin `/api/reconciliations` endpoint.
   - Pros: Smallest change, avoids CORS/file-origin issues, matches user-confirmed `http://127.0.0.1:8000/`, no new frontend toolchain, easy to test with `TestClient`.
   - Cons: Frontend behavior tests remain limited without a browser runner; inline JS can become harder to maintain if scope grows.
   - Effort: Low

2. **Static mount plus separated assets/scripts** — Mount `Frontend/` as static files and split JavaScript/CSS into separate files.
   - Pros: Cleaner frontend asset organization if future UI work expands.
   - Cons: More file movement and testing surface than needed; risks drifting from “minimal changes to existing visual design”.
   - Effort: Medium

3. **Introduce a frontend app/toolchain** — Convert to React/Vite or similar and consume the API.
   - Pros: Better long-term UI structure.
   - Cons: Explicitly out of scope; adds dependencies, build/run complexity, and review burden for a local MVP.
   - Effort: High

### Recommendation
Use Approach 1. Serve `Frontend/Diseño_mvp.html` directly from FastAPI at `/` and keep the browser request same-origin with `fetch('/api/reconciliations', { method: 'POST', body: formData })`. Add only the UI seams required for Phase 2: bank password input, submit disabled until both PDFs are selected, processing state during the request, visible error state for validation/API failures, ready state with a download link using the returned `download_url`, and reset/retry behavior as needed.

Testing should start with failing pytest tests before implementation: one contract test that `GET /` returns the HTML, one that the HTML contains the expected form controls/IDs or labels, and existing API tests to guard the multipart/download contract. Avoid changing service, scoring, compound detection, extraction, normalization, or Excel export tests except to keep them green.

### Risks
- `Frontend/Diseño_mvp.html` uses a non-ASCII filename; serving it via `Path(__file__)`-relative lookup is safer than relying on the process working directory.
- `UploadFile.filename` is used to build temp paths; Phase 2 should avoid expanding backend upload/path behavior unless tests explicitly require hardening.
- Browser-side validation must not replace backend validation; FastAPI should continue returning `422` for missing PDFs.
- Service failures currently return `500` JSON with `detail`; frontend must display that cleanly and not offer a stale download link.
- Download links should use the same-origin `download_url` returned by the API; hardcoding output filenames would couple frontend to backend internals.

### Ready for Proposal
Yes — the proposal should frame Phase 2 as a thin local integration layer: serve the existing static frontend from FastAPI, enhance the static HTML to call the existing API contract, and add pytest coverage around serving/contract behavior without introducing a frontend framework or touching reconciliation logic.
