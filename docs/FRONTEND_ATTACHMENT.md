# NeroSentinel web frontend

Date: 2026-10-08. The supplied web application is integrated under `frontend/`; the runnable build and browser-test work continued in this integrated copy, which is now authoritative and branded NeroSentinel. The existing FastAPI service remains the only backend.

## Implemented

- Replaced the default mock-first API client with a typed, error-aware client that requires the backend envelope. No silent mock fallback remains. Removed the unused California reservoir mock fixture.
- Connected overview, climate, water, risk map, digital twin, warnings, copilot, settings and simulator to the backend routes listed in `frontend/README.md`.
- Simulator uses a region-scoped researcher token to create and run two backend scenarios with matching horizons. Alert acknowledgement requires authority/admin scope. The token is pasted into Settings and stored only for the browser tab session; this is demo access, not production login.
- Corrected false UI claims: no invented drought probability, forecast confidence, live structural telemetry, California pilot, released NOAA calibration or automatic drought protocol. Synthetic/decision-support metadata is shown on data pages.
- Landing page includes the supplied GSAP ScrollTrigger + Lenis pinned image-mask concept: four themed chapters, locally authored SVG scenes, desktop pin/wipe/parallax, mobile interleaving and reduced-motion fallback. The existing Contribution Skyline remains available but is not populated with fake historical alert counts.
- Preserved Next.js 16.4/App Router, React Query, Zustand, Recharts, MapLibre and all backend contracts while applying the Forest & Sage visual system: local Anton/Inter fonts, exact earthy palette, fixed grain, rounded sections/cards, scroll reveals and reduced-motion support. Desktop glass-pill navigation becomes an accessible mobile drawer. No framework replacement was made.
- Preserved the concentric-ring and water-drop mark as a crisp transparent SVG for the website icon and both headers. Visible product naming is consistently NeroSentinel.

## Verification

- Frontend: `npx tsc --noEmit` and `npm run lint` passed in the supplied source folder after edits.
- Backend: 50 tests pass at 81% combined branch/statement coverage; the three frontend-contract tests cover all consumed read route envelopes, browser preflight, authenticated scenario creation/run and a bounded assistant response.
- Source parity: 38 relevant source/config files matched the edited export at copy time; the integrated copy now has its own Playwright tests and dependency metadata.
- Production Next build **passed** with Turbopack under unrestricted Windows access: latest build generated 12/12 app routes after replacing the default favicon. The earlier SWC canonicalization and `.next` `EPERM` failures were specific to the restricted sandbox; they did not reproduce with the same application/configuration after unrestricted access and a clean `npm ci`.
- Real HTTP checks passed for backend health/OpenAPI/docs and frontend routes. Thirteen Playwright browser checks passed against the production build, including authenticated scenarios, authorization failures, loading/error states, responsive home/dashboard/map layouts and local-only alert acknowledgement. See `INTEGRATED_VERIFICATION_2026-10-08.md`.

## Remaining boundaries

- The backend only has one synthetic Coimbatore pilot. The map marker is the pilot centroid, not a validated reservoir coordinate; map tiles require internet.
- No observed district data, historical daily alerts, live sensor telemetry, production identity, operational forecast calibration, public alert delivery or automatic water action exists.
- Production identity, observed-data validation, live feeds and external notification remain absent. The local demo build is runnable, but a public/operational deployment requires those controls plus TLS/reverse-proxy and target-host verification.
