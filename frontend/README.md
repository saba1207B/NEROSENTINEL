# NeroSentinel web frontend

This Next.js 16 application is connected to the existing FastAPI V2 service and branded NeroSentinel. This `frontend/` directory in the integrated deliverable is authoritative. No second backend was created.

## Run locally

1. Follow the integrated backend README to install Python and Node dependencies. From this directory, run `npm ci` and `npm run build`.
2. From the backend root, run `.\start-integrated.ps1` for the production build or `.\start-integrated.ps1 -Mode development` for Next dev. Open `http://127.0.0.1:3000/`. Stop with `.\stop-integrated.ps1`.
3. If the backend has a different address, copy `.env.example` to `.env.local`, change `NEXT_PUBLIC_API_BASE_URL`, and rebuild before starting production. The backend must allow the exact frontend origin in `CORS_ORIGINS`.
4. For scenario runs, create a local demo token in the backend with `python scripts/demo_token.py --role researcher`; paste it into `/dashboard/settings`. Alert acknowledgement requires an authority/admin token. Tokens are kept in tab session storage, not in source files or server logs.

The frontend does not silently fall back to mocks. If the API is unavailable, pages show an error. Browser map tiles use OpenStreetMap and require internet; scientific API values do not depend on map tiles.

## Connected routes

| UI | Backend |
| --- | --- |
| Overview | `/dashboard/summary`, `/reservoirs/demo-reservoir-1/forecast`, `/alerts` |
| Climate | `/enso/current`, `/enso/history`, `/forecasts` |
| Water | `/reservoirs`, `/water/demand`, `/water/balance` |
| Risk map | `/regions/tn-coimbatore`, `/reservoirs` |
| Digital twin | `/reservoirs/demo-reservoir-1`, `/reservoirs/demo-reservoir-1/forecast`, `/water/balance` |
| Simulator | `POST /scenarios`, `POST /scenarios/{id}/run` |
| Warnings | `/alerts`, `POST /alerts/{id}/acknowledge` |
| Copilot | `POST /assistant/query` |
| Settings | `/health`, `/sources` |

All backend calls expect its `{data, meta}` envelope. The UI displays synthetic provenance and avoids calling screening scores probabilities. The single pilot reservoir and map point are synthetic; there is no live telemetry, official boundary, trained predictive model, production login, public alert delivery, or automatic operating action. The copilot is a deterministic backend fallback, not a generative model.

The landing page incorporates the supplied pinned GSAP/Lenis image-mask story using four local SVG illustrations. The premium Forest & Sage system uses the exact forest/sage/olive/cream/moss palette, bundled Anton + Inter fonts, a 4% fixed grain texture, deeply rounded cards/sections, IntersectionObserver vertical reveals, and reduced-motion fallbacks. Desktop navigation is a fixed glass pill; mobile navigation is an accessible drawer. Product-style newsletter/cart patterns are omitted because this water-risk platform has no real signup or cart action. The concentric-ring/drop mark appears in both headers and the browser icon as `/nerosentinel-mark.svg`. The supplied Contribution Skyline component remains in `src/components/ui/` but is intentionally not shown as a year of alerts: the backend has no daily historical alert-count series to populate it truthfully.

## Verification

`npm run build`, `npx tsc --noEmit`, `npm run lint`, and the 13-test Playwright suite passed after rebranding. Tests verify the NeroSentinel browser title, header mark and icon, API hydration, security outcomes, responsive layout, and backend simulation consistency. Existing `AQUASENTINEL_*` test variable names and the `aquasentinel_demo_token` session key remain for compatibility. Never commit or print tokens. See `../docs/INTEGRATED_VERIFICATION_2026-10-08.md` and `../REBRANDING_REPORT.md` for verification details, compatibility exceptions, and limitations.
