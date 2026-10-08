# NeroSentinel release test results

Verification was performed on Windows on 2026-10-08 against the existing integrated source. These results are local checks, not a claim of public deployment readiness.

| Area | Command/check | Result |
|---|---|---|
| Frontend install | `npm ci` | 692 packages added; 693 audited. |
| Frontend production build | `npm run build` | Passed; Next.js 16.4/Turbopack generated 12/12 app routes. |
| Frontend lint | `npm run lint` | Passed. |
| Frontend types | `npx tsc --noEmit` | Passed. |
| Browser integration | `npm run test:e2e` with local role tokens | 13/13 Playwright tests passed against production Next.js and live FastAPI. |
| Backend tests | bundled Python `-m pytest -q` with `.deps;src` on `PYTHONPATH` | 50 passed; one Starlette/AnyIO deprecation warning. |
| Backend lint | bundled Python `-m ruff check src tests scripts` | Passed. |
| Fresh source install | `python -m venv .venv`, then `python -m pip install -e '.[dev]'` from a fresh ZIP extraction | Passed; the editable `nerosentinel` distribution and pinned runtime/dev dependencies installed in a clean Python 3.12.14 environment. |
| Fresh source tests | extracted release `python -m pytest -q`; `python -m ruff check src tests scripts` | 50 passed (one Starlette/AnyIO deprecation warning); Ruff passed. |
| Fresh source frontend | extracted release `npm ci`, `npm run build`, `npm run lint`, `npx tsc --noEmit` | Passed; 692 packages, 12/12 routes, lint and TypeScript clean. The same 9 high development-tool audit advisories remain. |
| Extracted-copy runtime | launched both services from the fresh extracted ZIP copy | Launcher readiness passed; health, OpenAPI, docs, homepage, dashboard, and SVG mark returned HTTP 200; OpenAPI title and page title were NeroSentinel. Original checkout services were restored afterward. |
| Database migrations | Alembic upgrade head → downgrade base → upgrade head on a new temporary SQLite database | Passed; no user database was touched. |
| HTTP runtime | launcher + HTTP checks | Health, OpenAPI JSON/docs, homepage, dashboard, climate and logo returned HTTP 200; OpenAPI title `NeroSentinel API`. |
| Auth/error paths | Playwright and API checks | Missing/invalid auth 401; unauthorized role 403; invalid assistant input 422; backend-unavailable/loading states checked. |
| Production dependency audit | `npm audit --omit=dev` | 0 vulnerabilities reported. |
| Full npm audit | `npm audit` | 9 high advisories remain in build/lint development tooling; see integrated verification. |

Docker/PostGIS/Redis execution, remote deployment/TLS, observed-data forecast validation, production identity, live telemetry, and external alert delivery were not verified or implemented. For the detailed commands, UI coverage, and scientific limitations see `INTEGRATED_VERIFICATION_2026-10-08.md`.
