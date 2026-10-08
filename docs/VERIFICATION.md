# V2 verification report

Date: 2026-10-08 (Asia/Calcutta). Commands below ran against this deliverable on the bundled Windows Python 3.12 runtime with `PYTHONPATH=.deps;src`.

## Regression and contracts

- `python -m pytest -q --cov=aquasentinel --cov-branch`: **50 passed** after frontend attachment. Combined statement/branch coverage **81%** (1,203 statements, 211 missed; 252 branches, 50 partial). The V1 source checkpoint measured 20 passed and 69% combined coverage (655 statements, 182 missed; 66 branches, 13 partial). Percentages are not directly comparable because V2 adds substantial code.
- `python -m ruff check src tests scripts`: all checks passed.
- `python scripts/export_openapi.py` and `python scripts/export_types.py`: generated `contracts/openapi.json` and `contracts/generated.ts`. The V2 contract contains **53 paths/operations**, including all **43 V1 paths** and 10 new paths; no V1 path was removed. This path-level comparison is not proof of every response field's semantic compatibility. Authentication changes are documented in `API_CONTRACT.md`.
- Scientific-engine checkpoint: 44 tests passed and 97% combined engine coverage. Hypothesis exercised 100 valid reservoir cases; see `SCIENTIFIC_VALIDATION.md`.
- `tests/test_frontend_contract.py`: three new tests pass for the consumed read routes, browser CORS preflight, researcher-token scenario create/run, and bounded assistant response.

## Database and runtime

- On a new SQLite verification database, `alembic upgrade head`, `alembic downgrade base`, and `alembic upgrade head` completed. Tables inspected: `alembic_version`, `data_sources`, `observations`, `regions`, `scenarios`.
- The PostgreSQL driver imports locally, but no PostgreSQL/PostGIS or Docker service was available; neither deployment nor PostgreSQL migration was verified.
- `run.ps1` reached Uvicorn `Application startup complete` on `127.0.0.1:8000`. A separate command session could not complete a loopback HTTP request in this sandbox, so cross-process serving is not counted as verified. FastAPI HTTP semantics were exercised by the test suite and the complete in-process TestClient demo. External authentication was not tested.

## Offline demonstration

`python scripts/demo_workflow.py` completed a synthetic monthly CSV ingestion, leakage-safe backtest, risk screen, baseline/intervention simulation, budgeted intervention plan, human approval record, action record, outcome reassessment record, provenance lookup and Tamil advisory.

- Ingestion status: `synthetic_user_supplied`; evaluation status: `research_evaluation_only`.
- Baseline total unmet demand: **131.6668 million m³**; intervention: **88.8276 million m³**. Both mass residuals: **0.0 million m³**.
- Plan status: `optimal_within_enumerated_options`; approval remains human-gated. The backend did **not** execute an operational release.
- These numbers describe a constructed example, not an observed benefit, calibrated prediction, or recommended real-world action.

## Performance and limitations

`python scripts/benchmark.py` produced local TestClient/CPU timings, recorded in `PERFORMANCE.md`. These are not deployment service-level results.

One Starlette TestClient/AnyIO deprecation warning is dependency-originated and did not fail tests. Live source adapters, observed validation, durable API repositories, production identity, external notification, and Docker runtime remain unverified or unimplemented as classified in `IMPLEMENTATION_STATUS.md`.

The attached frontend later passed `npm run build`, `npx tsc --noEmit`, `npm run lint`, and 12 Playwright checks in an unrestricted Windows run. FastAPI health/OpenAPI/docs and production Next routes returned HTTP 200. The earlier SWC/`.next` access failures and loopback timeouts were specific to the restricted sandbox and stale listeners; they did not reproduce after clean installation and fresh processes. The integrated Windows launcher was tested in both production and development modes. See `INTEGRATED_VERIFICATION_2026-10-08.md` for exact commands, security findings and remaining deployment boundaries.
