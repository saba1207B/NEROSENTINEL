# API contract and migration notes

Status: IMPLEMENTED for exported OpenAPI and TypeScript schema aliases; PARTIAL for fully typed operation responses.

The V1 OpenAPI checkpoint is in `work/baseline-v1/contracts/openapi.json` outside the deliverable. V2 retains every V1 path and adds ingestion, source registry, rolling backtest, FAO-56 ET0, intervention planning and approval tracking. `contracts/openapi.json` is exported from the running FastAPI application; `contracts/generated.ts` is generated from its component schemas. `contracts/types.ts` remains a compact hand-maintained frontend surface.

Successful responses retain `{ data, meta }`. Metadata adds `synthetic`, `geographic_resolution`, and `data_quality_status`. Source types add `unverified`. Scientific scenario results add valid-month and mass-ledger fields. Unknown artifact provenance now returns 404 instead of a fictitious fixture attribution. Forecast demo metadata now says `synthetic` rather than `forecast`.

Breaking authorization change: scenario mutations and readback, optimizations, alert rule/acknowledgement, reports and intervention actions require a bearer token with an allowed role and region. See `docs/FRONTEND_INTEGRATION.md`. Error responses are standardized as `{ error: { code, message, request_id, details } }`. The service does not yet generate a complete typed TypeScript client for every operation; use OpenAPI as the authoritative path/schema contract.

