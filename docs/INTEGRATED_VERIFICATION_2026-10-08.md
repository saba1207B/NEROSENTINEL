# NeroSentinel integrated verification

Date: 2026-10-08, Windows, local loopback. This report describes the NeroSentinel integrated deliverable in the existing `outputs/aquasentinel-backend` project folder, not an external deployment.

## Build-failure diagnosis

The previous restricted sandbox produced SWC path-canonicalization `Access is denied` and then `.next` `EPERM` directory-creation errors; it also could not reach stale localhost listeners. With unrestricted filesystem/network access, `npm ci` installed 692 packages (693 audited) in the integrated frontend and **the existing Next.js 16.4/Turbopack configuration built successfully without another application rewrite**. The latest NeroSentinel `npm run build` completed compilation, TypeScript, and static generation of 12/12 app routes. Earlier builds also passed before the default Next favicon route was retired in favor of the custom NeroSentinel SVG icon. Thus the reproduced build blocker was the earlier environment's filesystem/loopback restriction, not a defect in the current source. The earlier `next.config.ts` canonicalization issue had already been addressed by the integrated `next.config.mjs`; Google-font build downloads had already been removed. No error was suppressed to make the successful build pass.

## Commands and observed results

| Check | Command or request | Actual result |
| --- | --- | --- |
| Backend regression | `PYTHONPATH=.deps;src` then bundled Python `-m pytest -q --cov=aquasentinel --cov-branch` | 50 passed; 81% combined coverage (1,203 statements, 211 missed; 252 branches, 50 partial). One dependency-originated Starlette/AnyIO deprecation warning. |
| Backend lint | bundled Python `-m ruff check src tests scripts` | All checks passed. |
| Frontend install | `npm ci` | 692 packages added, 693 audited. |
| Frontend lint | `npm run lint` | Passed. |
| Frontend types | `npx tsc --noEmit` | Passed. |
| Production build | `npm run build` | Passed; latest Next.js 16.4.0/Turbopack build generated 12/12 app routes, including all dashboard routes. |
| HTTP runtime | `Invoke-WebRequest` to health, OpenAPI JSON, docs, landing page, dashboard and climate | HTTP 200 for all six endpoints. After launcher testing, health, OpenAPI, landing and settings also returned HTTP 200. |
| Windows launcher | `.\start-integrated.ps1`, `.\stop-integrated.ps1`, `.\start-integrated.ps1 -Mode development` | Production and development modes both passed readiness checks; recorded stop shut down each session; production mode was started again and left running. |
| Browser integration | `npm run test:e2e` with local researcher and authority demo tokens in environment variables | 13/13 Playwright tests passed against production Next and live FastAPI. |

## Forest & Sage UI verification

The existing dashboard and landing routes now share the requested Forest & Sage design system rather than replacing the app architecture: bundled local Anton/Inter fonts, exact palette tokens, 4% fixed SVG grain, rounded cards/sections, the requested reveal easing, scroll-triggered section reveals, reduced-motion behavior, and a responsive glass navigation. Dashboard pages retain their existing backend data contracts and scientific caveats. The landing page omits a fake newsletter/cart action; it links to actual modules. Local SVG climate/reservoir art is used instead of unverified remote imagery. Playwright checks the homepage, dashboard, and map for document overflow at 320, 375, 430, 768, 1024, 1440, and 1920 pixel viewport widths and exercises the mobile navigation. The suite verifies UI behavior and API consistency, not scientific validity of the synthetic model.

The browser tests exercise all nine dashboard areas; synthetic-data labels; real API hydration; CORS preflight; 401 missing/invalid bearer; 422 invalid assistant input; no-token simulation refusal; backend-unavailable and delayed-loading states; water search and map marker popup; settings retry; bounded assistant response; researcher scenario creation/run; backend trajectory total and mass-residual consistency; researcher 403 on alert acknowledgement; local authority acknowledgement; design tokens, grain and font; NeroSentinel header logo, favicon, title and metadata; absence of former product naming in the UI; responsive widths; scroll reveal; reduced motion; and mobile navigation. Tests are in `frontend/tests/e2e/integration.spec.ts`. The scenario test checks that displayed unmet-demand totals came from the two actual backend run responses, each 12-month trajectory sums to its declared total within 1e-6 MCM, and the backend mass-balance residual is below 1e-6 MCM. This is a consistency check on the synthetic model, not scientific validation against observations.

## Verified local addresses

- Production frontend: `http://127.0.0.1:3000/`
- Backend health: `http://127.0.0.1:8000/api/v1/health`
- OpenAPI JSON: `http://127.0.0.1:8000/api/v1/openapi.json`
- Interactive API docs: `http://127.0.0.1:8000/api/docs`

The final production launcher session records its exact process IDs under ignored `runtime/session.json`; `.\stop-integrated.ps1` stops that recorded process tree after checking creation times. Do not copy the runtime logs or local tokens into a repository.

## Security and deployment boundaries

- `npm audit --omit=dev` reported **0 vulnerabilities** after classifying the build-only `shadcn` CLI/CSS package as a dev dependency. Full `npm audit` still reported **9 high** advisories in build/lint tooling through `braces`/`micromatch`/`fast-glob`, including `shadcn` and `eslint-config-next`. `npm view braces version` reported 3.0.3, the audited vulnerable version, so no nonbreaking upstream fix was available in this run. No forced major downgrade or audit suppression was applied. Reassess before public CI/build deployment.
- The backend's default JWT secret and demo-token issuer are for trusted local demo mode only. Production identity integration is not implemented. Mutating routes remain bearer/role/region gated; tests confirmed 401 and 403 paths.
- The frontend's `NEXT_PUBLIC_API_BASE_URL` is compiled into the browser bundle. Set it before `npm run build` for a different API host, and configure backend `CORS_ORIGINS` for the exact frontend origin. The local browser/CORS path was verified; remote-origin deployment was not.
- Synthetic Coimbatore pilot values are consistently labeled. The map marker uses a synthetic pilot centroid, not a surveyed reservoir coordinate. External OpenStreetMap tile availability and appearance were not verified as an offline guarantee. No observed forecast skill, live telemetry, production login, public alert delivery, or automatic operating action is claimed.
- Docker/PostGIS/Redis deployment, TLS/reverse proxy, external domain hosting, production secret management, live-feed adapters and real-user acceptance were not exercised in this run. The result is a runnable and browser-verified **local demonstration**, not an operational/public deployment approval.

## Repeat the browser suite

With both services running, generate local demo tokens in a backend shell with its Python environment active, assign them to `AQUASENTINEL_TEST_RESEARCHER_TOKEN` and `AQUASENTINEL_TEST_AUTHORITY_TOKEN` without printing or saving them, then run `npm run test:e2e` inside `frontend/`. If tokens are absent, the three role-dependent browser tests are explicitly skipped. Chrome is required by `frontend/playwright.config.ts`; use another installed Chromium channel there if needed.
