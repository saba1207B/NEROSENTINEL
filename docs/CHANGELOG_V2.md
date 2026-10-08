# V2 source change inventory

Compared byte-for-byte with the preserved V1 source checkpoint. Generated caches, local dependencies and verification databases are excluded.

## Backend code

- Changed: `src/aquasentinel/config.py`, `main.py`, `schemas.py`, `security.py`, `store.py`.
- Changed: `src/aquasentinel/engines/enso.py`, `optimization.py`, `risk.py`, `simulation.py`, `water.py`.
- Added: `src/aquasentinel/units.py`, `ingestion.py`, `engines/forecast.py`, `engines/interventions.py`.

## Contracts, scripts, deployment and fixtures

- Changed: `contracts/openapi.json`, `contracts/types.ts`, `data/fixtures/pilot_manifest.json`, `docker-compose.yml`, `README.md`, `run.ps1`, `test.ps1`, `scripts/demo_workflow.py`.
- Added: `contracts/generated.ts`, `scripts/benchmark.py`, `scripts/demo_token.py`, `scripts/export_types.py`.

## Tests

- Changed: `tests/test_api.py`.
- Added: `tests/test_precision.py`.
- Existing `tests/test_engines.py` and `tests/test_security.py` remain unchanged and still pass.

## Documentation

- Changed: `docs/FRONTEND_INTEGRATION.md`, `IMPLEMENTATION_STATUS.md`, `SCIENTIFIC_ASSUMPTIONS.md`, `VERIFICATION.md`.
- Added: `docs/API_CONTRACT.md`, `AUDIT_REPORT.md`, `DATA_PROVENANCE.md`, `MODEL_EVALUATION.md`, `OPTIMIZATION_VALIDATION.md`, `PERFORMANCE.md`, `PHYSICAL_ASSUMPTIONS.md`, `SCIENTIFIC_VALIDATION.md`, `SECURITY_AUDIT.md`, `CHANGELOG_V2.md`.

No V1 OpenAPI path was removed. Authentication requirements and some metadata semantics changed; see `API_CONTRACT.md`.
