# Reconciliation Orchestration Service Specification

## Purpose

Define the backend-only callable boundary that runs the existing local reconciliation pipeline without import-time side effects or business-rule changes.

## Requirements

### Requirement: Import-Safe Backend Modules

Backend modules that participate in orchestration MUST be safe to import without opening PDFs, printing extracted tables, running reconciliation, or writing Excel files.

#### Scenario: Importing orchestration modules

- GIVEN the backend service, bank extractor, ERP extractor, and main entry module exist
- WHEN a test imports those modules
- THEN no PDF file is opened
- AND no reconciliation or Excel export is executed

#### Scenario: Demo or CLI behavior is explicit

- GIVEN a module contains sample/demo execution
- WHEN the module is imported by service or API code
- THEN the demo behavior MUST NOT run unless explicitly invoked

### Requirement: Parameterized Nequi PDF Password

The Nequi bank PDF extraction MUST accept the caller-provided bank PDF password and MUST NOT use a hardcoded password for extraction.

#### Scenario: Password is forwarded

- GIVEN a bank PDF path and password are provided
- WHEN Nequi extraction is invoked
- THEN the PDF reader receives that same password

#### Scenario: Password is optional at service boundary

- GIVEN no bank password is provided
- WHEN the service calls bank extraction
- THEN the absence of password is forwarded explicitly
- AND no hardcoded fallback password is used

### Requirement: Callable Pipeline With Output Path

The service MUST expose a callable reconciliation operation accepting ERP PDF path, bank PDF path, optional bank password, and optional Excel output path, while preserving existing extraction, normalization, reconciliation, compound detection, and Excel export behavior.

#### Scenario: Successful reconciliation

- GIVEN valid local ERP and bank PDF paths and an output path
- WHEN the service runs reconciliation
- THEN the existing pipeline steps are invoked in order
- AND the Excel exporter receives the requested output path

#### Scenario: Default output path

- GIVEN valid inputs and no output path
- WHEN the service runs reconciliation
- THEN an `.xlsx` output path is produced and returned to the caller

### Requirement: Service Verification Expectations

Service changes MUST be covered by pytest tests using fakes or monkeypatches rather than mandatory real-PDF fixtures.

#### Scenario: Fast boundary tests

- GIVEN the service tests run with monkeypatched pipeline functions
- WHEN `python -m pytest -q` is executed
- THEN import safety, password forwarding, call order, and output path behavior are verified
- AND existing reconciliation and Excel tests remain green
