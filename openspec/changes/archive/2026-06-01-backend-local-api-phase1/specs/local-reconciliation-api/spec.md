# Local Reconciliation API Specification

## Purpose

Define a local-only backend API contract for a future frontend to submit PDFs, pass the bank password, trigger reconciliation, and discover the generated Excel result.

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

### Requirement: Excel Result Metadata Contract

The API response MUST expose enough metadata for a future frontend to locate or download the generated workbook without changing the Excel workbook layout.

#### Scenario: Output metadata returned

- GIVEN reconciliation completes successfully
- WHEN the API builds the response
- THEN it includes the generated `.xlsx` filename or path
- AND MAY include a local download URL and row/count metadata

#### Scenario: Extraction or service failure

- GIVEN extraction or reconciliation fails
- WHEN the service reports the failure
- THEN the API returns an error response without pretending completion

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

API behavior MUST be covered by pytest contract tests with a local test client and monkeypatched service.

#### Scenario: Contract tests cover request and response shape

- GIVEN the service is replaced with a fake
- WHEN API tests submit valid and invalid multipart requests
- THEN validation, password forwarding, service invocation, and response metadata are verified
- AND no real PDF parsing is required
