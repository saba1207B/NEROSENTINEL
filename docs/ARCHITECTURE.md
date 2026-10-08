# Architecture

NeroSentinel is a modular monolith. HTTP contracts, scientific engines, persistence models, and infrastructure adapters are separate boundaries inside one deployable service. This keeps local development simple while allowing expensive workers or adapters to be extracted later. The Python import package remains `aquasentinel` for compatibility.

```text
FastAPI /api/v1
  -> validated Pydantic contracts
  -> deterministic engines (ENSO, risk, water balance, digital twin, LP)
  -> repository boundary (thread-safe demo store / SQLAlchemy production models)
  -> PostgreSQL/PostGIS, Redis, object storage adapters
```

The current offline path uses a reproducible synthetic fixture and a thread-safe in-memory scenario repository. SQLAlchemy 2 models and the first Alembic migration establish durable region, source, observation, and scenario storage. PostGIS and Redis are provisioned in Compose; live geospatial ingestion and distributed workers remain Phase 2/3 work.

## Scientific safety boundaries

- ENSO is a covariate, never a deterministic local cause.
- The groundwater index is not water volume.
- Flood output is not advertised because hydraulic inputs are absent.
- Scenario frequencies depend on declared distributions and are not assigned probabilities for named climate futures.
- Optimization outputs require qualified human approval.
- The assistant is read-only and deterministic when no local LLM is configured.
