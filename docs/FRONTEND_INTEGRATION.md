# Frontend integration

Base URL: `http://127.0.0.1:8000/api/v1`

The supplied Next.js frontend is now included at `../frontend`. Its route map and verification are in `FRONTEND_ATTACHMENT.md`. Local CORS permits `http://localhost:3000` and `http://127.0.0.1:3000` by default.

Every successful response uses `{ data, meta }`. Inspect `meta.source_type`, `synthetic`, `data_quality_status`, `limitations`, `sources`, and `units` before presenting a value. `unverified` marks quarantined user uploads. Never remove synthetic or decision-support labels in the UI.

Scenario, optimization, ingestion, alert mutation, report and intervention workflow routes require `Authorization: Bearer <token>` with a region-scoped researcher, authority or admin role. Approval, action and outcome routes require authority/admin. In local demo mode, issue an ephemeral researcher token with `python scripts/demo_token.py --role researcher`; authority token issuance is for a local trusted reviewer only. No token issuance endpoint or production identity provider is included.

Core judge flow:

1. `GET /dashboard/summary`
2. `POST /scenarios` with `{ "name": "Deficit", "rainfall_multiplier": 0.7, "demand_growth": 0.08 }`
3. `POST /scenarios/{id}/run`
4. `POST /scenarios/compare` with two to four complete scenario objects
5. `POST /optimizations` with water availability and sector demand, or `POST /optimizations/interventions` with user-supplied costs, budget and rainfall cases
6. `POST /advisories/preview`
7. `GET /provenance/fixture-tn-v1`
8. For a review trail: `POST /interventions/proposals`, then authority-only `POST /interventions/{id}/approve`, `/action-record`, and `/outcome`

Use the `X-Request-ID` header for correlation and `Idempotency-Key` when creating scenarios. The compact TypeScript interfaces are in `contracts/types.ts`; generated schema types are in `contracts/generated.ts`, and the complete machine-readable contract is `contracts/openapi.json`.
