# NeroSentinel · Intelligent Water Intelligence & Drought Resilience Platform

An offline-first FastAPI decision-support backend for a synthetic Tamil Nadu water-resilience pilot. V2 adds explicit physical units, corrected reservoir accounting, local data quarantine, leakage-safe baseline evaluation, FAO-56 ET0, budgeted intervention search and authorization gates.

The integrated Next.js web application and existing FastAPI V2 service form NeroSentinel. The frontend consumes the backend's actual `{data, meta}` contract rather than defaulting to invented mock responses. All bundled pilot values remain synthetic and explicitly identified.

## Install and run on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
cd frontend
npm ci
npm run build
cd ..
.\start-integrated.ps1
```

The launcher starts the production frontend at `http://127.0.0.1:3000/`, the NeroSentinel API at `http://127.0.0.1:8000/api/v1/health`, and OpenAPI docs at `http://127.0.0.1:8000/api/docs`. It checks both services over HTTP and writes process IDs and logs under ignored `runtime/`. Stop with `.\stop-integrated.ps1`. For development mode, run `.\start-integrated.ps1 -Mode development` after `npm ci`; a production build is not required. The launcher refuses occupied ports instead of attaching to an unknown process.

Run backend tests with `./test.ps1`. After activating an environment with the project dependencies installed, run the complete offline demonstration with:

```powershell
$env:PYTHONPATH = "src"
python scripts/demo_workflow.py
```

State-changing API calls require a bearer token. In local demo mode, run `python scripts/demo_token.py --role researcher` with the project environment active. Keep the token private. Production identity integration is not implemented.

The frontend defaults to `http://127.0.0.1:8000/api/v1`; for another backend address, set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` **before building** and rebuild. Also set backend `CORS_ORIGINS` to the exact frontend origin. Paste an ephemeral demo token into the frontend Settings page to run scenarios. See `frontend/README.md` and `docs/INTEGRATED_VERIFICATION_2026-10-08.md` for the route mapping, executed checks and limits.

For a conventional Python environment on another machine, use Python 3.11+ and Node.js 20.9+:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn aquasentinel.main:app --reload
```

## Docker

Copy `.env.example` to `.env`, replace `JWT_SECRET` and `POSTGRES_PASSWORD` with private random values, then run `docker compose up --build`. Compose binds the API to host loopback and includes PostGIS and Redis. Local API execution does not require either service in demo mode. Docker execution has not been verified on this host.

## Truthfulness

All bundled environmental records are synthetic and labeled as such. Uploaded records remain unverified and quarantined. No model is described as trained, no pilot forecast accuracy is claimed, and optimization/release results are not automatic operating instructions. See `docs/IMPLEMENTATION_STATUS.md` for exact boundaries and `docs/VERIFICATION.md` for executed checks.

The production build and local HTTP/browser integration are verified for the **offline demo**. This is not an operational/public deployment: production identity, observed-data validation, live source feeds, TLS/reverse-proxy deployment and external notification have not been implemented or verified. Keep `DEMO_MODE` enabled only in a trusted local environment. See the integrated verification report before deploying anywhere else.

## Compatibility identifiers retained during rebrand

The Python import package/module path (`aquasentinel`), default SQLite filename, Compose PostgreSQL database/user and named volume, JWT issuer/audience, Prometheus metric names, browser session token key, and `AQUASENTINEL_*` test/API environment variables retain their existing identifiers to avoid breaking imports, persisted databases, issued development tokens, dashboards, and local tooling. The frontend build/package and installed Python distribution are named `nerosentinel`; no user-visible product branding retains the former name. See `docs/REBRANDING_REPORT.md` and `docs/INTEGRATED_VERIFICATION_2026-10-08.md` for audit details.
