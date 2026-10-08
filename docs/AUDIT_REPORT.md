# V2 baseline forensic audit

Audit date: 2026-10-08. This historical V2 baseline audit is retained as provenance; its pre-rebrand checkpoint was stored outside the portable source release. Classification reflects inspected code, not the prior report.

## Baseline verification

- Scientific engine tests: 11 passed when run separately.
- Full checkpoint suite: 20 passed after allowing local sockets needed by Python's Windows event loop.
- Baseline coverage measured with `pytest --cov=aquasentinel --cov-branch`: 655 statements, 182 missed; 66 branches, 13 partial; 69% combined coverage (72% statement coverage).
- OpenAPI: 43 declared paths. The initially suspected static scenario route shadowing was disproved by authenticated requests to both `compare` and `monte-carlo`; Starlette continues route matching after a method mismatch.
- SQL schema: four domain tables and Alembic revision `0001_core`; scenario API uses memory, so SQL persistence is not wired into requests.
- Datasets: only synthetic constants and a manifest. No observed ingestion, calibration, or trained model exists.

## Findings

| Priority | Finding | Evidence / impact |
| --- | --- | --- |
| P0 | Reservoir evaporation/loss can exceed available water; negative physical balance is clipped and residual then hidden by `max(0, expected)`. | `engines/water.py` |
| P0 | Nonfinite floats enter Pydantic numeric fields and scientific engine arguments. | `schemas.py`, `engines/water.py`, `engines/enso.py` |
| P0 | Mutating scenario, alert, optimization and advisory endpoints have no JWT verification or role checks. | `main.py`; `security.py` only signs tokens. |
| P1 | `budget_million_inr` is accepted but ignored by optimization; no actual cost decision variable exists. | `engines/optimization.py` |
| P1 | Reservoir ledger reports gross release but not delivered volume and conveyance loss separately. | `engines/simulation.py` |
| P1 | Synthetic ENSO endpoint reports a fabricated confidence number and synthetic history adds fixed 30-day increments. | `main.py`, `engines/enso.py` |
| P1 | `/provenance/{artifact_id}` returns the same fabricated processing story for any ID. | `main.py` |
| P1 | `/reports/{id}` and `/optimizations/{id}` return placeholder not-persisted records. | `main.py` |
| P1 | `Dockerfile` runs as nonroot but Compose config uses a placeholder JWT secret; PostGIS/Redis are provisioned yet not used by API. | `Dockerfile`, `docker-compose.yml` |
| P2 | Minimal tests miss edge cases, property checks, authorization and route reachability. | `tests/` |
| P2 | OpenAPI responses are weakly typed because endpoint return types are mostly generic. | `main.py` |

## Scientific classification

- Implemented physical calculation: single reservoir step and lumped monthly water balance, subject to P0 repair.
- Screening: drought score, groundwater index, ENSO classification and correlation.
- Synthetic demonstration: all pilot data and scenario forecasts.
- Blocked on authorized observed data: calibration, forecast skill, real district selection and operational warnings.

## Package and performance status

- Python 3.12 local target dependencies exist in `.deps`; no version conflict was observed during scientific test execution.
- Baseline API request performance was unmeasured; V2 local measurements are recorded in `PERFORMANCE.md`. Docker is not installed here.
- Monte Carlo is a Python loop over simulations. Profiling is required before optimization.
