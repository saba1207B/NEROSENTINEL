# NeroSentinel rebrand audit

## Result

The existing AquaSentinel application was rebranded in place as **NeroSentinel**. Its FastAPI + Next.js architecture, API paths and payloads, scientific engines, data provenance, and security gates were retained. User-visible application metadata, navigation/headers, footer and status text, app/package distribution names, API title/description, custom SVG favicon/logo, Postman collection name, Docker user, and documentation were updated. The exact platform tagline is **Intelligent Water Intelligence & Drought Resilience Platform**.

The mark is `frontend/public/nerosentinel-mark.svg`, the supplied water-drop/rings motif rendered as a vector with transparent background. The original starter favicon was removed from active routing; the custom SVG is used instead.

## Compatibility choices

`aquasentinel` remains the Python import package and Uvicorn module path. Existing database filenames/default names, Compose PostgreSQL database/user and named volume, JWT issuer/audience, Prometheus metric names, browser session key `aquasentinel_demo_token`, and `AQUASENTINEL_*` test/API environment variables are retained. These identifiers are internal compatibility contracts, not user-facing branding. No database schema or migration, route, or authorization relaxation was introduced. Compose now requires an explicit `POSTGRES_PASSWORD`; use a private URL-safe value in `.env`.

The old name also appears in historical changelog/scientific reports, source paths, test assertions that enforce absence of old branding in rendered UI, and docs explaining the compatibility identifiers. These references are intentionally preserved rather than performing a risky global replacement. A scan of active source found no old product name in the rendered application; Playwright asserted that absence across the dashboard routes.

## Scope and verification

The verified pre-rebrand checkpoint contained 143 project files. Against that checkpoint, 25 existing files changed (including user-visible names, frontend metadata/brand assets, distribution/API names, docs and release security configuration), two new documentation files were added, and the logo and Postman collection were renamed. The starter favicon and generated TypeScript build-info artifact are not part of the release. The ZIP contains 143 source/document/config files, excluding dependency trees, virtual environments, caches/bytecode, runtime logs/process state, databases, and the local work directory. It includes `.env.example` only; no local secrets or credentials are packaged. This is a source-code release, not a license grant; the original project had no `LICENSE` file.

Build, test, browser, HTTP, security, scientific-consistency, and deployment limitations are detailed in `TEST_RESULTS.md` and `INTEGRATED_VERIFICATION_2026-10-08.md`. The available evidence supports a runnable local demo, not production/public deployment readiness.
