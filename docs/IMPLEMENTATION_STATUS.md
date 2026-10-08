# NeroSentinel V2 implementation status

## IMPLEMENTED and verified

- FastAPI service, consistent metadata/error contracts, correlation/security headers
- JWT verification with region and role gates for consequential demo APIs; in-memory audit events
- Canonical volume/area/rainfall conversions, finite input validation, and loss-aware reservoir mass balance
- Per-month digital twin ledger, shortage onset, bounds, deterministic scenario comparison
- CSV quarantine with size, schema, checksum, duplicate, gap and range checks
- Leakage-safe rolling monthly climatology and persistence backtesting functions
- FAO-56 daily Penman-Monteith ET0 endpoint validated against a published example
- Budget-bounded discrete intervention planning across declared rainfall cases
- Proposal, approval, action-record and outcome-reassessment state transitions
- Offline synthetic Tamil Nadu pilot manifest
- ENSO threshold screening and lagged-correlation analysis
- Reservoir mass balance with dead-storage/capacity constraints
- Deterministic district-scale digital twin and scenario comparison
- Seeded Monte Carlo uncertainty propagation
- Transparent drought screening and groundwater index
- Linear-programming water allocation with infeasibility reporting
- Deterministic English/Tamil/Hindi safety advisory templates
- Read-only deterministic assistant fallback
- SQLAlchemy core entities, reversible Alembic migration, Docker/Compose recipe, Prometheus endpoint
- OpenAPI and generated TypeScript component contracts, automated unit/API/security/property tests

## PARTIAL or demonstration only

- Persistence: schemas exist; scenario demo execution uses memory for zero-setup operation.
- Authentication: JWT authorization is enforced on selected consequential endpoints; persistent users, login/OIDC, refresh and revocation are absent.
- Geospatial: valid GeoJSON delivery exists, using a declared synthetic rectangle rather than official boundaries.
- Forecasting: rolling backtesting code exists; the pilot still lacks authorized observed series and no active predictive model is validated.
- Reports: JSON evidence report metadata exists; PDF generation is planned.
- Intervention workflow and audit records are in memory and disappear on restart.
- Allocation budget is not used by the legacy LP because it has no cost variables; V2 discrete intervention planning does use caller-supplied decimal costs.

## BLOCKED by unavailable data or infrastructure

- Live NOAA/IMD/NASA/WRIS/CWC/CGWB ingestion adapters; source documentation has been reviewed, but pilot data access, terms and suitability remain unverified.
- Observed calibration and historical pilot validation
- Observed-data training/backtesting, XGBoost/PyTorch/SHAP model registry artifacts
- Raster processing, official boundaries, hydraulic flood extent modeling
- Docker runtime verification (Docker is unavailable in this environment)

## PLANNED

- Durable SQL repositories for API scenarios, ingestions, optimizations, approvals and audit history
- Celery workers, MinIO artifact store, real email/SMS/push delivery
- OIDC integration, production rate limiter, refresh/revocation and account management
- Persisted intervention feedback with revision-aware outcome evaluation
- Official boundaries, raster processing and hydraulic flood models when data permits
- Local Ollama tool-calling adapter after source and permission checks

These omissions are deliberate scope boundaries. The service makes no claim that they work.
