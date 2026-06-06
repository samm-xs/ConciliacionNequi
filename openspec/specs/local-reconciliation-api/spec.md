# Local Reconciliation API Specification

## Purpose

Define a local-only backend API contract for a frontend to submit PDFs, pass the bank password, trigger reconciliation, and discover or download the generated Excel result.

## Requirements

### Requirement: Local API Reconciliation Endpoint

The backend API MUST provide a local-only reconciliation endpoint that accepts multipart PDF inputs and forwards validated data to the orchestration service.

#### Scenario: Successful API request

- GIVEN multipart fields `erp_pdf`, `bank_pdf`, and optional `password_banco` or equivalent are provided
- WHEN the client submits a reconciliation request
- THEN the API calls the service with local file paths and the provided password
- AND returns status `completed` with Excel output metadata

#### Scenario: Missing required PDFs

- GIVEN either PDF field is missing
- WHEN the client submits a reconciliation request
- THEN the API MUST return a validation error
- AND the service MUST NOT be called

### Requirement: Local Static Frontend Serving

The backend MUST serve the existing static MVP HTML from `GET /` for local browser use, without requiring a frontend build toolchain or changing reconciliation business logic.

#### Scenario: Frontend page served locally

- GIVEN the local FastAPI app is running
- WHEN a user requests `/`
- THEN the response MUST return the static MVP HTML successfully
- AND the existing API routes MUST remain available.

#### Scenario: Local-only frontend scope

- GIVEN the frontend is served by the backend
- WHEN the page loads
- THEN it MUST NOT require React, Vite, deployment, authentication, database, or cloud storage.

### Requirement: Browser Reconciliation Form

The frontend MUST expose user inputs for ERP PDF, bank PDF, and bank password, and MUST submit those values as multipart `FormData` to same-origin `POST /api/reconciliations` using fields `erp_pdf`, `bank_pdf`, and `password_banco`.

#### Scenario: Valid browser submission

- GIVEN ERP PDF, bank PDF, and a bank password are entered
- WHEN the user submits the form
- THEN the browser MUST call `/api/reconciliations` with the required `FormData` field names.

#### Scenario: Missing PDF before submission

- GIVEN either PDF is not selected
- WHEN the user attempts to submit
- THEN the UI MUST show a missing-file state
- AND MUST NOT start a reconciliation request.

### Requirement: Frontend Request States

The frontend MUST clearly represent missing-files, processing, error, and ready/download states, and MUST clear stale errors or download links when a new request starts or fails.

#### Scenario: Processing state

- GIVEN both PDFs are selected
- WHEN the reconciliation request is in progress
- THEN the UI MUST show processing feedback
- AND prevent duplicate submission.

#### Scenario: API error state

- GIVEN the API returns validation or service failure
- WHEN the frontend receives the response
- THEN it MUST display a clear error
- AND MUST NOT show a stale download link.

### Requirement: Excel Result Metadata Contract

The API response MUST expose enough metadata for the local frontend to download the generated workbook without changing the Excel workbook layout, including a `download_url` when reconciliation completes successfully.

#### Scenario: Output metadata returned

- GIVEN reconciliation completes successfully
- WHEN the API builds the response
- THEN it includes the generated `.xlsx` filename or path
- AND MUST include a local download URL and MAY include row/count metadata.

#### Scenario: Extraction or service failure

- GIVEN extraction or reconciliation fails
- WHEN the service reports the failure
- THEN the API returns an error response without pretending completion

### Requirement: Excel Download From API Metadata

The frontend MUST use the API response `download_url` as the Excel download target after a successful reconciliation.

#### Scenario: Ready download state

- GIVEN the API returns a successful response with `download_url`
- WHEN the frontend renders completion
- THEN it MUST show a ready/download state
- AND the download action MUST point to that `download_url`.

#### Scenario: Missing download URL

- GIVEN the API response lacks `download_url`
- WHEN the frontend handles completion
- THEN it MUST report an error instead of hardcoding a workbook path.

### Requirement: Dependency Manifest and Local Run Support

The backend MUST provide a dependency manifest and local run instructions for the selected local API runtime and existing reconciliation libraries.

#### Scenario: Fresh local setup

- GIVEN a developer has Python available locally
- WHEN dependencies are installed from the manifest
- THEN the local API and existing pytest suite can be run without undocumented packages

#### Scenario: Scope remains local-only

- GIVEN the API is started for Phase 1
- WHEN it serves requests
- THEN it MUST NOT require authentication, database, cloud storage, deployment, or frontend implementation

### Requirement: API Verification Expectations

API and local frontend contract behavior MUST be covered by pytest tests with a local test client and monkeypatched service; static expectations MAY be checked through served HTML or markup assertions without adding a browser runner.

#### Scenario: Contract tests cover request and response shape

- GIVEN the service is replaced with a fake
- WHEN API tests submit valid and invalid multipart requests
- THEN validation, password forwarding, service invocation, and response metadata are verified
- AND no real PDF parsing is required

#### Scenario: Static frontend contract tests

- GIVEN pytest uses the local test client
- WHEN tests request `/` and inspect the static contract
- THEN frontend serving, required fields, submit behavior seams, and `download_url` usage expectations are verified.
