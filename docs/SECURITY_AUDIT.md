# Security audit

Status: IMPLEMENTED for bearer verification and region/role gates on consequential demo APIs; PARTIAL for production identity and persistence.

The API verifies JWT signature, issuer, audience, issuance and expiry, then checks role and region scope for scenario creation/execution/readback, optimization, alert mutation, report mutation, and intervention approval/action/outcome records. Tests cover missing, invalid and expired tokens, viewer denial, wrong-region denial and authority-only approval. Scenario idempotency keys are scoped to actor and checked against the original payload. Consequential actions produce an in-memory audit event.

Demo token generation is a local CLI convenience and is disabled outside demo mode. Compose requires a configured JWT secret and binds its host port to loopback. The service does not provide a public demo token endpoint or send external notifications.

Remaining P1/P2 gaps: no persisted user directory, OIDC login, refresh/revocation mechanism, durable audit ledger, distributed rate limit, production secret manager, or region boundary authorization beyond the single pilot. The in-memory repository loses state on restart and is unsuitable for operational approval records. Treat the service as a secure research/demo foundation, not a production authority system.

