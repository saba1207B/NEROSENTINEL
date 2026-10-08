from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from aquasentinel import __version__
from aquasentinel.config import get_settings
from aquasentinel.engines.advisory import render_advisory
from aquasentinel.engines.enso import classify_enso, lagged_teleconnection
from aquasentinel.engines.forecast import rolling_monthly_baselines
from aquasentinel.engines.interventions import plan_interventions
from aquasentinel.engines.optimization import optimize_allocation
from aquasentinel.engines.risk import drought_risk
from aquasentinel.engines.simulation import monte_carlo, simulate_scenario
from aquasentinel.engines.water import (
    fao56_reference_et0,
    penman_monteith_daily_et0,
    reservoir_step,
)
from aquasentinel.ingestion import MAX_CSV_BYTES, ingest_monthly_csv
from aquasentinel.schemas import (
    ActionRecordCreate,
    AdvisoryRequest,
    ApiResponse,
    AssistantQuery,
    BacktestRequest,
    Fao56DailyInputs,
    InterventionPlanRequest,
    MonteCarloRequest,
    OptimizationRequest,
    OutcomeCreate,
    ProposalCreate,
    Region,
    ResponseMeta,
    ScenarioCreate,
    SourceRef,
    SourceType,
)
from aquasentinel.security import Actor, authorize
from aquasentinel.store import store

settings = get_settings()
REQUESTS = Counter("aquasentinel_http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("aquasentinel_http_request_duration_seconds", "HTTP latency", ["path"])

PILOT = Region(id="tn-coimbatore", name="Coimbatore synthetic pilot", region_type="district", state="Tamil Nadu", area_km2=4723, centroid=(11.0168, 76.9558))
DEMO_SOURCE = SourceRef(source_id="fixture-tn-v1", name="NeroSentinel reproducible synthetic pilot fixture", license="CC0-1.0", observation_period="12-month synthetic seasonal profile; no historical observations")
ONI_SOURCE = SourceRef(source_id="fixture-oni-v1", name="Synthetic ONI-like demonstration series", license="CC0-1.0", observation_period="demo only")
NOW = datetime(2026, 10, 8, 7, 0, tzinfo=UTC)


def meta(*, region_id: str | None = None, source_type: SourceType = SourceType.SYNTHETIC, model: str | None = None, confidence: float | None = None, limitations: list[str] | None = None, sources: list[SourceRef] | None = None, units: dict[str, str] | None = None, synthetic: bool = True, data_quality_status: str | None = None) -> ResponseMeta:
    resolution = ("district-scale synthetic pilot" if synthetic else "user-declared region; resolution unverified") if region_id else None
    return ResponseMeta(region_id=region_id, source_type=source_type, data_as_of=NOW if synthetic else datetime.now(UTC), model_version=model, confidence=confidence, limitations=limitations or [], sources=[DEMO_SOURCE] if sources is None else sources, units=units or {}, synthetic=synthetic, geographic_resolution=resolution, data_quality_status=data_quality_status or ("synthetic" if synthetic else "user_supplied_unverified"))


def envelope(data: object, **kwargs: object) -> ApiResponse:
    return ApiResponse(data=data, meta=meta(**kwargs))


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="NeroSentinel API",
    description="Intelligent Water Intelligence & Drought Resilience Platform. Offline-first decision support; demonstration responses are synthetic and never operational instructions.",
    version=__version__,
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    with LATENCY.labels(request.url.path).time():
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    REQUESTS.labels(request.method, request.url.path, response.status_code).inc()
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    details = [{"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]} for item in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "request_id": request_id, "details": details}})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": f"HTTP_{exc.status_code}", "message": str(exc.detail), "request_id": request_id, "details": []}})


@app.get("/api/v1/health", tags=["system"])
def health():
    return envelope({"status": "healthy", "version": __version__, "mode": "offline_demo" if settings.demo_mode else "configured"}, source_type=SourceType.MODELED, sources=[])


@app.get("/api/v1/ready", tags=["system"])
def ready():
    return envelope({"status": "ready", "checks": {"api": "ok", "demo_store": "ok"}, "external_dependencies_required": False}, source_type=SourceType.MODELED, sources=[])


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/regions", tags=["regions"])
def regions(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    items = [PILOT][offset:offset + limit]
    return envelope({"items": items, "total": 1, "limit": limit, "offset": offset}, region_id=PILOT.id)


@app.get("/api/v1/regions/{region_id}", tags=["regions"])
def region(region_id: str):
    _require_region(region_id)
    return envelope(PILOT, region_id=region_id)


@app.get("/api/v1/dashboard/summary", tags=["dashboard"])
def dashboard_summary():
    risk = drought_risk(-28, -22, 0.49, 0.46)
    return envelope({"region": PILOT, "enso": classify_enso([0.6, 0.7, 0.8, 0.9, 0.8]), "water": {"reservoir_storage_mcm": 51.5, "capacity_fraction": 0.49, "groundwater_index": 0.46}, "risk": risk, "active_alerts": 2}, region_id=PILOT.id, model="drought-screen-v1", limitations=["Synthetic pilot values; not current Coimbatore conditions."], units={"reservoir_storage_mcm": "million cubic metres"})


@app.get("/api/v1/enso/current", tags=["enso"])
def enso_current():
    values = [0.6, 0.7, 0.8, 0.9, 0.8]
    return envelope({**classify_enso(values), "oni_last_five_c": values, "influence_note": "ENSO is one covariate. Local monsoon dynamics, land conditions, and water management can dominate local outcomes."}, model="enso-threshold-screen-v2", confidence=None, sources=[ONI_SOURCE], limitations=["Synthetic ONI-like input; not a live NOAA classification."], units={"oni_last_five_c": "degrees Celsius anomaly"})


@app.get("/api/v1/enso/history", tags=["enso"])
def enso_history():
    values = [-0.4, -0.2, 0.0, 0.2, 0.6, 0.7, 0.8, 0.9, 0.8]
    return envelope({"items": [{"month": date(2026 + i // 12, i % 12 + 1, 1).isoformat(), "oni_c": value} for i, value in enumerate(values)]}, sources=[ONI_SOURCE], units={"oni_c": "degrees Celsius anomaly"})


@app.get("/api/v1/enso/teleconnections", tags=["enso"])
def enso_teleconnections():
    enso = [-0.6, -0.4, -0.1, 0.2, 0.5, 0.8, 0.9, 0.7, 0.3, -0.1, -0.4, -0.7] * 2
    rainfall = [18, 22, 30, 32, 28, 20, 17, 18, 26, 36, 42, 38] * 2
    return envelope({"region_id": PILOT.id, "lagged_correlations": lagged_teleconnection(enso, rainfall), "interpretation": "Exploratory correlation from synthetic data; correlation is not causation or predictive skill."}, region_id=PILOT.id, model="pearson-lag-screen-v1", sources=[DEMO_SOURCE], limitations=["Sample size is small and synthetic."])


@app.get("/api/v1/forecasts", tags=["forecasts"])
def forecasts():
    return envelope({"items": [{"id": "seasonal-climatology-demo-v1", "region_id": PILOT.id, "horizon_days": 90, "rainfall_anomaly_pct": -22, "interval_pct": [-45, 8], "status": "baseline_demo"}]}, region_id=PILOT.id, source_type=SourceType.SYNTHETIC, model="seasonal-climatology-v1", confidence=None, limitations=["Demonstration baseline is not trained on observed pilot data and has no operational forecast skill claim."])


@app.post("/api/v1/forecasts/backtest", tags=["forecasts"])
def forecast_backtest(payload: BacktestRequest, actor: Actor):
    _require_region(payload.region_id)
    authorize(actor, payload.region_id, {"researcher", "authority", "admin"})
    try:
        result = rolling_monthly_baselines(
            [(item.month, item.rainfall_mm) for item in payload.observations], payload.min_train
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    source = SourceRef(source_id=payload.source_id, name="User declared synthetic monthly series" if payload.synthetic else "User supplied unverified monthly series")
    status_label = "synthetic_user_supplied" if payload.synthetic else "user_supplied_unverified"
    return envelope(result, region_id=payload.region_id, source_type=SourceType.MODELED, model="rolling-baselines-v1", sources=[source], synthetic=payload.synthetic, data_quality_status=status_label, limitations=["Input series is user supplied and not independently verified; metrics do not establish operational skill."])


@app.get("/api/v1/sources", tags=["provenance"])
def sources():
    return envelope({"items": [
        {"id": "fixture-tn-v1", "status": "implemented_synthetic", "mode": "offline_fixture"},
        {"id": "noaa-enso", "status": "documentation_reviewed_adapter_not_implemented", "url": "https://psl.noaa.gov/data/timeseries/month/"},
        {"id": "noaa-roni", "status": "documentation_reviewed_adapter_not_implemented", "url": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/announcement.php"},
        {"id": "nasa-power", "status": "documentation_reviewed_adapter_not_implemented", "url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"},
        {"id": "chirps-v3", "status": "documentation_reviewed_adapter_not_implemented", "url": "https://chc.ucsb.edu/data/chirps3"},
        {"id": "imd-cwc-cgwb-indiawris", "status": "official_export_required_access_unverified"},
    ]}, source_type=SourceType.MODELED, sources=[], synthetic=False, data_quality_status="source_registry_only")


@app.post("/api/v1/ingestion/monthly-csv", tags=["ingestion"])
async def ingest_csv(request: Request, actor: Actor, source_id: str = Header(..., alias="X-Source-ID"), region_id: str = Header(..., alias="X-Region-ID"), x_synthetic_data: bool = Header(False, alias="X-Synthetic-Data")):
    _require_region(region_id)
    authorize(actor, region_id, {"researcher", "authority", "admin"})
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_CSV_BYTES:
            raise HTTPException(413, "CSV exceeds 2 MB limit")
        chunks.append(chunk)
    try:
        result = ingest_monthly_csv(b"".join(chunks), source_id=source_id, region_id=region_id, declared_synthetic=x_synthetic_data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    store.ingestions[f"{result['checksum_sha256']}:{result['verification_status']}"] = result
    store.audit(actor["sub"], "ingestion.quarantine", result["checksum_sha256"])
    summary = {key: value for key, value in result.items() if key != "records"}
    return envelope(summary, region_id=region_id, source_type=SourceType.SYNTHETIC if x_synthetic_data else SourceType.UNVERIFIED, sources=[SourceRef(source_id=source_id, name="User supplied synthetic CSV" if x_synthetic_data else "User supplied unverified CSV")], synthetic=x_synthetic_data, data_quality_status=result["verification_status"], limitations=["Quarantined for provenance review; not used for active forecasts."])


@app.get("/api/v1/forecasts/{forecast_id}", tags=["forecasts"])
def forecast(forecast_id: str):
    if forecast_id != "seasonal-climatology-demo-v1":
        raise HTTPException(404, "forecast not found")
    return forecasts()


@app.get("/api/v1/risks", tags=["risks"])
def risks(rainfall_anomaly_pct: float = Query(-28, ge=-100), soil_moisture_anomaly_pct: float = Query(-22, ge=-100)):
    return envelope({"items": [drought_risk(rainfall_anomaly_pct, soil_moisture_anomaly_pct, 0.49, 0.46)]}, region_id=PILOT.id, source_type=SourceType.MODELED, model="drought-screen-v1", limitations=["Screening severity is not a calibrated probability."])


@app.get("/api/v1/risks/compare", tags=["risks"])
def risks_compare():
    return envelope({"items": [{"label": "baseline", **drought_risk(-10, -8, 0.7, 0.6)}, {"label": "deficit", **drought_risk(-35, -30, 0.4, 0.4)}]}, region_id=PILOT.id, source_type=SourceType.MODELED, model="drought-screen-v1")


@app.get("/api/v1/risks/{region_id}", tags=["risks"])
def risk_by_region(region_id: str):
    _require_region(region_id)
    return risks()


@app.get("/api/v1/water/balance", tags=["water"])
def water_balance():
    step = reservoir_step(51.5, 105, 8.2, 13, 1.4, 0.5, 8)
    return envelope(step.__dict__, region_id=PILOT.id, source_type=SourceType.MODELED, model="reservoir-mass-balance-v1", units={"storage_mcm": "million cubic metres", "spill_mcm": "million cubic metres", "release_mcm": "million cubic metres"})


@app.get("/api/v1/water/demand", tags=["water"])
def water_demand():
    sectors = {"domestic_mcm": 4.2, "agriculture_mcm": 10.8, "industrial_mcm": 1.9, "environmental_mcm": 1.1}
    return envelope({"sectors": sectors, "total_mcm": round(sum(sectors.values()), 2), "assumptions": {"distribution_loss_fraction": 0.18, "basis": "synthetic monthly pilot coefficients"}}, region_id=PILOT.id, units={"*_mcm": "million cubic metres per month"})


@app.get("/api/v1/reservoirs", tags=["reservoirs"])
def reservoirs():
    return envelope({"items": [{"id": "demo-reservoir-1", "name": "Synthetic Pilot Reservoir", "capacity_mcm": 105, "storage_mcm": 51.5, "dead_storage_mcm": 8}]}, region_id=PILOT.id, units={"capacity_mcm": "million cubic metres", "storage_mcm": "million cubic metres"})


@app.get("/api/v1/reservoirs/{reservoir_id}", tags=["reservoirs"])
def reservoir(reservoir_id: str):
    _require_reservoir(reservoir_id)
    return reservoirs()


@app.get("/api/v1/reservoirs/{reservoir_id}/forecast", tags=["reservoirs"])
def reservoir_forecast(reservoir_id: str):
    _require_reservoir(reservoir_id)
    result = simulate_scenario(ScenarioCreate(name="reservoir baseline", months=6))
    return envelope({"reservoir_id": reservoir_id, "trajectory": result.trajectory, "reliability": result.reliability}, region_id=PILOT.id, source_type=SourceType.MODELED, model="digital-twin-v1", limitations=result.assumptions)


@app.get("/api/v1/groundwater", tags=["groundwater"])
def groundwater():
    return envelope({"region_id": PILOT.id, "groundwater_index": 0.46, "classification": "stressed", "volume_claim": False, "explanation": "The dimensionless index combines synthetic normalized level and recharge signals; aquifer storage volume is not inferred."}, region_id=PILOT.id, model="groundwater-screen-v1", limitations=["No aquifer specific yield or transmissivity is available in the demo."])


@app.get("/api/v1/groundwater/trends", tags=["groundwater"])
def groundwater_trends():
    return envelope({"values": [{"month": i + 1, "index": round(0.62 - i * 0.014, 3)} for i in range(12)], "trend_per_month": -0.014}, region_id=PILOT.id, model="groundwater-linear-screen-v1")


@app.get("/api/v1/agriculture/crop-risk", tags=["agriculture"])
def crop_risk(crop: str = Query("paddy", pattern="^(paddy|sugarcane|groundnut|millets|pulses)$")):
    factors = {"paddy": 0.82, "sugarcane": 0.88, "groundnut": 0.52, "millets": 0.31, "pulses": 0.47}
    return envelope({"crop": crop, "water_stress_score": factors[crop], "screening_only": True, "factors": ["synthetic soil moisture deficit", "seasonal water availability", "generic crop sensitivity"]}, region_id=PILOT.id, model="crop-screen-v1", limitations=["Crop stage, field soil, and observed weather are not available."])


@app.post("/api/v1/agriculture/irrigation-scenario", tags=["agriculture"])
def irrigation_scenario(temp_min_c: float = 22, temp_max_c: float = 34, temp_mean_c: float = 28, solar_radiation_mj_m2_day: float = Query(18, ge=0), crop_coefficient: float = Query(1.05, ge=0, le=2.5)):
    try:
        et0 = fao56_reference_et0(temp_min_c, temp_max_c, temp_mean_c, solar_radiation_mj_m2_day)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return envelope({"reference_et0_mm_day": et0, "crop_et_mm_day": round(et0 * crop_coefficient, 4), "method": "legacy empirical radiation screening proxy", "operational_schedule": False}, region_id=PILOT.id, model="et-screen-v1", limitations=["This empirical proxy is not FAO-56 or calibrated crop ET. Use the FAO-56 endpoint when complete inputs exist."], units={"reference_et0_mm_day": "millimetres per day", "crop_et_mm_day": "millimetres per day"})


@app.post("/api/v1/agriculture/et0/fao56", tags=["agriculture"])
def fao56_et0(payload: Fao56DailyInputs):
    try:
        et0 = penman_monteith_daily_et0(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return envelope({"reference_et0_mm_day": et0, "method": "FAO-56 daily Penman-Monteith", "operational_schedule": False}, region_id=PILOT.id, source_type=SourceType.MODELED, model="fao56-pm-v1", limitations=["Output quality depends on representative measured meteorological inputs; no pilot calibration is available."], units={"reference_et0_mm_day": "millimetres per day"})


@app.post("/api/v1/scenarios", tags=["scenarios"], status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioCreate, actor: Actor, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    _require_region(payload.region_id)
    authorize(actor, payload.region_id, {"researcher", "authority", "admin"})
    if idempotency_key and len(idempotency_key) > 128:
        raise HTTPException(422, "idempotency key too long")
    try:
        record, created = store.create_scenario(payload, actor["sub"], idempotency_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if created:
        store.audit(actor["sub"], "scenario.create", str(record.id))
    return envelope(record, region_id=record.region_id)


@app.get("/api/v1/scenarios/{scenario_id}", tags=["scenarios"])
def get_scenario(scenario_id: UUID, actor: Actor):
    record = store.scenarios.get(scenario_id)
    if not record:
        raise HTTPException(404, "scenario not found")
    authorize(actor, record.region_id, {"researcher", "authority", "admin"})
    return envelope(record, region_id=record.region_id)


@app.post("/api/v1/scenarios/{scenario_id}/run", tags=["scenarios"])
def run_scenario(scenario_id: UUID, actor: Actor):
    record = store.scenarios.get(scenario_id)
    if not record:
        raise HTTPException(404, "scenario not found")
    authorize(actor, record.region_id, {"researcher", "authority", "admin"})
    payload = ScenarioCreate(**record.model_dump(exclude={"id", "status", "created_at"}))
    result = store.save_result(scenario_id, simulate_scenario(payload))
    store.audit(actor["sub"], "scenario.run", str(scenario_id))
    return envelope(result, region_id=record.region_id, source_type=SourceType.MODELED, model="digital-twin-v1", limitations=result.assumptions)


@app.get("/api/v1/scenarios/{scenario_id}/results", tags=["scenarios"])
def scenario_results(scenario_id: UUID, actor: Actor):
    if scenario_id not in store.results:
        raise HTTPException(404, "scenario result not found; run the scenario first")
    result = store.results[scenario_id]
    authorize(actor, result.region_id, {"researcher", "authority", "admin"})
    return envelope(result, region_id=result.region_id, source_type=SourceType.MODELED, model="digital-twin-v1", limitations=result.assumptions)


@app.post("/api/v1/scenarios/compare", tags=["scenarios"])
def compare_scenarios(payload: list[ScenarioCreate], actor: Actor):
    if not 2 <= len(payload) <= 4:
        raise HTTPException(422, "compare between two and four scenarios")
    for item in payload:
        _require_region(item.region_id)
        authorize(actor, item.region_id, {"researcher", "authority", "admin"})
    results = [simulate_scenario(item) for item in payload]
    return envelope({"items": [{"name": item.name, "reliability": result.reliability, "total_unmet_mcm": result.total_unmet_mcm, "end_storage_mcm": result.trajectory[-1].storage_mcm} for item, result in zip(payload, results, strict=True)]}, region_id=payload[0].region_id, source_type=SourceType.MODELED, model="digital-twin-v1")


@app.post("/api/v1/scenarios/monte-carlo", tags=["scenarios"])
def run_monte_carlo(payload: MonteCarloRequest, actor: Actor):
    _require_region(payload.scenario.region_id)
    authorize(actor, payload.scenario.region_id, {"researcher", "authority", "admin"})
    result = monte_carlo(payload.scenario, payload.iterations, payload.rainfall_std_fraction, payload.demand_std_fraction)
    return envelope(result, region_id=payload.scenario.region_id, source_type=SourceType.MODELED, model="monte-carlo-v1", limitations=["Intervals depend on user-declared normal input distributions."])


@app.post("/api/v1/optimizations", tags=["optimization"])
def optimize(payload: OptimizationRequest, actor: Actor):
    _require_region(payload.region_id)
    authorize(actor, payload.region_id, {"researcher", "authority", "admin"})
    result = optimize_allocation(payload)
    optimization_id = uuid4()
    store.optimizations[optimization_id] = {"id": optimization_id, "region_id": payload.region_id, **result}
    store.audit(actor["sub"], "optimization.propose", payload.region_id)
    return envelope(store.optimizations[optimization_id], region_id=payload.region_id, source_type=SourceType.MODELED, model="allocation-lp-v1", limitations=["Priority weights and minimum allocations are policy assumptions requiring authority review."])


@app.post("/api/v1/optimizations/interventions", tags=["optimization"])
def optimize_interventions(payload: InterventionPlanRequest, actor: Actor):
    _require_region(payload.scenario.region_id)
    authorize(actor, payload.scenario.region_id, {"researcher", "authority", "admin"})
    result = plan_interventions(payload)
    plan_id = uuid4()
    result = {"id": plan_id, "region_id": payload.scenario.region_id, **result}
    store.optimizations[plan_id] = result
    store.audit(actor["sub"], "intervention.plan", payload.scenario.region_id)
    return envelope(result, region_id=payload.scenario.region_id, source_type=SourceType.MODELED, model="intervention-enumeration-v1", limitations=result["limitations"])


@app.post("/api/v1/interventions/proposals", tags=["interventions"], status_code=201)
def propose_intervention(payload: ProposalCreate, actor: Actor):
    plan = store.optimizations.get(payload.plan_id)
    if plan is None:
        raise HTTPException(404, "plan not found")
    region_id = plan["region_id"]
    authorize(actor, region_id, {"researcher", "authority", "admin"})
    if plan["status"] not in {"optimal", "optimal_within_enumerated_options"}:
        raise HTTPException(409, "infeasible plan cannot be proposed")
    proposal_id = uuid4()
    item = {"id": proposal_id, "region_id": region_id, "plan_id": payload.plan_id, "responsible_authority": payload.responsible_authority, "review_by": payload.review_by, "rationale": payload.rationale, "status": "proposed", "proposed_by": actor["sub"], "created_at": datetime.now(UTC), "operational_action_executed": False}
    store.proposals[proposal_id] = item
    store.audit(actor["sub"], "intervention.propose", str(proposal_id))
    return envelope(item, region_id=region_id, source_type=SourceType.MODELED, model="approval-workflow-v1")


@app.get("/api/v1/interventions/{proposal_id}", tags=["interventions"])
def intervention_status(proposal_id: UUID, actor: Actor):
    item = store.proposals.get(proposal_id)
    if item is None:
        raise HTTPException(404, "proposal not found")
    authorize(actor, item["region_id"], {"researcher", "authority", "admin"})
    return envelope(item, region_id=item["region_id"], source_type=SourceType.MODELED, model="approval-workflow-v1")


@app.post("/api/v1/interventions/{proposal_id}/approve", tags=["interventions"])
def approve_intervention(proposal_id: UUID, actor: Actor):
    item = store.proposals.get(proposal_id)
    if item is None:
        raise HTTPException(404, "proposal not found")
    authorize(actor, item["region_id"], {"authority", "admin"})
    if item["status"] != "proposed":
        raise HTTPException(409, "proposal is not awaiting approval")
    item.update(status="approved", approved_by=actor["sub"], approved_at=datetime.now(UTC))
    store.audit(actor["sub"], "intervention.approve", str(proposal_id))
    return envelope(item, region_id=item["region_id"], source_type=SourceType.MODELED, model="approval-workflow-v1")


@app.post("/api/v1/interventions/{proposal_id}/action-record", tags=["interventions"])
def record_intervention_action(proposal_id: UUID, payload: ActionRecordCreate, actor: Actor):
    item = store.proposals.get(proposal_id)
    if item is None:
        raise HTTPException(404, "proposal not found")
    authorize(actor, item["region_id"], {"authority", "admin"})
    if item["status"] != "approved":
        raise HTTPException(409, "proposal must be approved before an action is recorded")
    item.update(status="action_recorded", action_record=payload.model_dump(mode="json"), recorded_by=actor["sub"])
    store.audit(actor["sub"], "intervention.action_record", str(proposal_id))
    return envelope(item, region_id=item["region_id"], source_type=SourceType.UNVERIFIED, synthetic=False, model="approval-workflow-v1", limitations=["Action is self-reported; NeroSentinel did not execute or independently verify it."])


@app.post("/api/v1/interventions/{proposal_id}/outcome", tags=["interventions"])
def record_intervention_outcome(proposal_id: UUID, payload: OutcomeCreate, actor: Actor):
    item = store.proposals.get(proposal_id)
    if item is None:
        raise HTTPException(404, "proposal not found")
    authorize(actor, item["region_id"], {"authority", "admin"})
    if item["status"] != "action_recorded":
        raise HTTPException(409, "action record is required before outcome assessment")
    plan = store.optimizations[item["plan_id"]]
    expected = plan.get("planned", {}).get("worst_case_unmet_mcm")
    item.update(status="reassessment_due", outcome=payload.model_dump(mode="json"), expected_unmet_mcm=expected, observed_minus_expected_mcm=None if expected is None else round(payload.observed_unmet_mcm - expected, 4), outcome_recorded_by=actor["sub"])
    store.audit(actor["sub"], "intervention.outcome", str(proposal_id))
    return envelope(item, region_id=item["region_id"], source_type=SourceType.SYNTHETIC if payload.synthetic else SourceType.UNVERIFIED, synthetic=payload.synthetic, sources=[SourceRef(source_id=payload.observation_source_id, name="User supplied outcome source")], model="approval-workflow-v1", limitations=["Outcome source is user supplied and not independently verified; reassessment is required."])


@app.get("/api/v1/optimizations/{optimization_id}", tags=["optimization"])
def optimization_status(optimization_id: UUID, actor: Actor):
    result = store.optimizations.get(optimization_id)
    if result is None:
        raise HTTPException(404, "optimization not found")
    authorize(actor, result["region_id"], {"researcher", "authority", "admin"})
    model = "intervention-enumeration-v1" if result["status"] == "optimal_within_enumerated_options" else "allocation-lp-v1"
    return envelope(result, region_id=result["region_id"], source_type=SourceType.MODELED, model=model)


@app.get("/api/v1/geospatial/layers", tags=["geospatial"])
def geospatial_layers():
    return envelope({"items": [{"id": "pilot-region", "geometry_type": "Polygon", "crs": "EPSG:4326", "status": "synthetic_simplified"}, {"id": "pilot-reservoir", "geometry_type": "Point", "crs": "EPSG:4326", "status": "synthetic"}]}, region_id=PILOT.id)


@app.get("/api/v1/geospatial/regions/{region_id}", tags=["geospatial"])
def region_geojson(region_id: str):
    _require_region(region_id)
    lon, lat = PILOT.centroid[1], PILOT.centroid[0]
    geometry = {"type": "Polygon", "coordinates": [[[lon - .3, lat - .25], [lon + .3, lat - .25], [lon + .3, lat + .25], [lon - .3, lat + .25], [lon - .3, lat - .25]]]}
    return envelope({"type": "Feature", "id": region_id, "properties": {"name": PILOT.name, "synthetic_geometry": True}, "geometry": geometry}, region_id=region_id, limitations=["Simplified synthetic rectangle; not an administrative boundary."])


@app.get("/api/v1/alerts", tags=["alerts"])
def alerts():
    items = list(store.alerts.values()) or [{"id": "demo-low-storage", "type": "reservoir_shortage", "severity": "high", "status": "open", "delivery_mode": "local_test_only", "region_id": PILOT.id}]
    return envelope({"items": items}, region_id=PILOT.id)


@app.post("/api/v1/alerts/rules", tags=["alerts"])
def create_alert_rule(actor: Actor, threshold: float = Query(..., ge=0, le=1), cooldown_hours: int = Query(24, ge=1, le=720)):
    authorize(actor, PILOT.id, {"authority", "admin"})
    rule_id = str(uuid4())
    rule = {"id": rule_id, "metric": "reservoir_capacity_fraction", "operator": "lt", "threshold": threshold, "cooldown_hours": cooldown_hours, "enabled": True, "notification_mode": "local_test_only"}
    store.alerts[rule_id] = rule
    store.audit(actor["sub"], "alert.rule.create", rule_id)
    return envelope(rule, region_id=PILOT.id)


@app.post("/api/v1/alerts/{alert_id}/acknowledge", tags=["alerts"])
def acknowledge_alert(alert_id: str, actor: Actor):
    authorize(actor, PILOT.id, {"authority", "admin"})
    alert = store.alerts.get(alert_id)
    if alert is None and alert_id != "demo-low-storage":
        raise HTTPException(404, "alert not found")
    result = dict(alert or {"id": alert_id, "type": "reservoir_shortage", "severity": "high"}, status="acknowledged", acknowledged_at=datetime.now(UTC))
    store.alerts[alert_id] = result
    store.audit(actor["sub"], "alert.acknowledge", alert_id)
    return envelope(result, region_id=PILOT.id)


@app.get("/api/v1/advisories", tags=["advisories"])
def advisories():
    return envelope({"items": [render_advisory(AdvisoryRequest())]}, region_id=PILOT.id)


@app.post("/api/v1/advisories/preview", tags=["advisories"])
def advisory_preview(payload: AdvisoryRequest):
    return envelope(render_advisory(payload), region_id=payload.region_id)


@app.post("/api/v1/assistant/query", tags=["assistant"])
def assistant_query(payload: AssistantQuery):
    _require_region(payload.region_id)
    question = payload.question.lower()
    if "why" in question or "drought" in question:
        answer = "The synthetic pilot screening score rises because rainfall, soil moisture, reservoir storage, and the groundwater index are all below their reference levels. ENSO is only a contextual factor and is not treated as the sole cause."
        evidence = ["artifact:risk-demo-v1", "artifact:fixture-tn-v1"]
    elif "uncertain" in question or "uncertainty" in question:
        answer = "Uncertainty comes from input measurements, simplified model structure, scenario assumptions, and natural climate variability. Run the Monte Carlo endpoint to propagate declared rainfall and demand ranges."
        evidence = ["model:digital-twin-v1"]
    else:
        answer = "I can explain drought drivers, uncertainty, scenario comparisons, and intervention trade-offs using the authorized demo artifacts. I cannot trigger operations or public warnings."
        evidence = []
    return envelope({"answer": answer, "citations": evidence, "mode": "deterministic_fallback", "can_trigger_operations": False}, region_id=payload.region_id, source_type=SourceType.MODELED, model="copilot-rules-v1")


@app.post("/api/v1/reports", tags=["reports"])
def create_report(actor: Actor, region_id: str = PILOT.id):
    _require_region(region_id)
    authorize(actor, region_id, {"researcher", "authority", "admin"})
    report_id = uuid4()
    report = {"id": report_id, "region_id": region_id, "status": "completed", "format": "json", "sections": ["status", "risk", "assumptions", "provenance"], "note": "PDF rendering is planned; this is a synthetic JSON evidence summary."}
    store.reports[report_id] = report
    store.audit(actor["sub"], "report.create", str(report_id))
    return envelope(report, region_id=region_id)


@app.get("/api/v1/reports/{report_id}", tags=["reports"])
def report(report_id: UUID, actor: Actor):
    item = store.reports.get(report_id)
    if item is None:
        raise HTTPException(404, "report not found")
    authorize(actor, item["region_id"], {"researcher", "authority", "admin"})
    return envelope(item, region_id=item["region_id"])


@app.get("/api/v1/provenance/{artifact_id}", tags=["provenance"])
def provenance(artifact_id: str):
    if artifact_id == "fixture-tn-v1":
        source, processing = DEMO_SOURCE, ["declared synthetic fixture profile"]
    elif artifact_id == "fixture-oni-v1":
        source, processing = ONI_SOURCE, ["declared synthetic ONI-like sequence"]
    elif artifact_id == "risk-demo-v1":
        source, processing = DEMO_SOURCE, ["weighted drought screening calculation"]
    else:
        try:
            scenario_id = UUID(artifact_id)
        except ValueError as exc:
            raise HTTPException(404, "artifact provenance not found") from exc
        if scenario_id in store.results:
            source, processing = DEMO_SOURCE, ["scenario parameter validation", "monthly mass-balance simulation"]
        elif scenario_id in store.optimizations:
            source, processing = DEMO_SOURCE, ["declared optimization inputs", "constraint solving or option enumeration"]
        elif scenario_id in store.proposals:
            source, processing = DEMO_SOURCE, ["modeled plan reference", "human review state recording"]
        else:
            raise HTTPException(404, "artifact provenance not found")
    return envelope({"artifact_id": artifact_id, "dataset": source, "processing": processing, "synthetic": True, "training_period": None, "validation_metrics": None, "integrity": {"fixture_version": "1.0.0", "status": "declared_synthetic"}}, source_type=SourceType.SYNTHETIC, sources=[source])


@app.get("/api/v1/models", tags=["models"])
def models():
    items = [
        {"id": "digital-twin-v1", "kind": "deterministic", "trained": False, "status": "implemented"},
        {"id": "drought-screen-v1", "kind": "explicit weighted index", "trained": False, "status": "implemented"},
        {"id": "allocation-lp-v1", "kind": "linear optimization", "trained": False, "status": "implemented"},
        {"id": "intervention-enumeration-v1", "kind": "bounded discrete optimization", "trained": False, "status": "implemented_demo"},
        {"id": "rolling-baselines-v1", "kind": "chronological baseline evaluation", "trained": False, "status": "research_evaluation_only"},
        {"id": "fao56-pm-v1", "kind": "physical reference evapotranspiration", "trained": False, "status": "implemented"},
        {"id": "seasonal-climatology-v1", "kind": "forecast baseline", "trained": False, "status": "demonstration_only"},
    ]
    return envelope({"items": items}, source_type=SourceType.MODELED, sources=[])


@app.get("/api/v1/models/{model_id}/metrics", tags=["models"])
def model_metrics(model_id: str):
    implemented = {"digital-twin-v1", "drought-screen-v1", "allocation-lp-v1", "intervention-enumeration-v1", "rolling-baselines-v1", "fao56-pm-v1", "seasonal-climatology-v1"}
    if model_id not in implemented:
        raise HTTPException(404, "model not found")
    return envelope({"model_id": model_id, "predictive_metrics": None, "validation": "Scientific invariant tests only" if model_id != "seasonal-climatology-v1" else "Not fitted or backtested", "accuracy_claimed": False}, source_type=SourceType.MODELED, sources=[])


def _require_region(region_id: str) -> None:
    if region_id != PILOT.id:
        raise HTTPException(404, "region not found")


def _require_reservoir(reservoir_id: str) -> None:
    if reservoir_id != "demo-reservoir-1":
        raise HTTPException(404, "reservoir not found")
