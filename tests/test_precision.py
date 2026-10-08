from datetime import UTC, date, datetime, timedelta
from math import isfinite

import jwt
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from aquasentinel.config import get_settings
from aquasentinel.engines.enso import classify_enso, lagged_teleconnection
from aquasentinel.engines.forecast import rolling_monthly_baselines
from aquasentinel.engines.interventions import plan_interventions
from aquasentinel.engines.optimization import optimize_allocation
from aquasentinel.engines.risk import drought_risk
from aquasentinel.engines.simulation import PilotParameters, simulate_scenario
from aquasentinel.engines.water import (
    fao56_reference_et0,
    penman_monteith_daily_et0,
    reservoir_step,
)
from aquasentinel.ingestion import ingest_monthly_csv
from aquasentinel.main import app
from aquasentinel.schemas import (
    InterventionPlanRequest,
    OptimizationRequest,
    ScenarioCreate,
    SectorDemand,
)
from aquasentinel.security import create_access_token
from aquasentinel.units import flow_to_volume_m3, m3_to_mcm, mcm_to_m3, rainfall_volume_m3

client = TestClient(app)


def headers(role: str = "researcher") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token('precision-test', [role], ['tn-coimbatore'])}"}


def month(index: int) -> date:
    return date(2020 + index // 12, index % 12 + 1, 1)


def test_canonical_unit_conversions_and_incident_rainfall() -> None:
    assert mcm_to_m3(1) == 1_000_000
    assert m3_to_mcm(1_000_000) == 1
    assert rainfall_volume_m3(10, 1_000_000) == 10_000
    assert flow_to_volume_m3(2, 86_400) == 172_800
    with pytest.raises(ValueError):
        rainfall_volume_m3(-1, 100)


def test_loss_requests_exceeding_available_water_are_disclosed() -> None:
    result = reservoir_step(2, 100, 0, 10, 5, 2)
    assert result.storage_mcm == 0
    assert result.release_mcm == 0
    assert result.evaporation_mcm == 2
    assert result.evaporation_shortfall_mcm == 3
    assert result.other_losses_shortfall_mcm == 2
    assert abs(result.mass_balance_error_mcm) < 1e-10


@given(
    storage=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    capacity=st.floats(min_value=1000, max_value=2000, allow_nan=False, allow_infinity=False),
    inflow=st.floats(min_value=0, max_value=2000, allow_nan=False, allow_infinity=False),
    release=st.floats(min_value=0, max_value=2000, allow_nan=False, allow_infinity=False),
    evaporation=st.floats(min_value=0, max_value=2000, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100, deadline=None)
def test_reservoir_mass_conservation_property(
    storage: float, capacity: float, inflow: float, release: float, evaporation: float
) -> None:
    result = reservoir_step(storage, capacity, inflow, release, evaporation)
    assert 0 <= result.storage_mcm <= capacity + 1e-9
    assert result.release_mcm >= 0
    assert isfinite(result.storage_mcm)
    residual = storage + inflow - result.evaporation_mcm - result.other_losses_mcm - result.release_mcm - result.spill_mcm - result.storage_mcm
    assert abs(residual) <= 1e-8 * max(1, storage + inflow)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_values_are_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        reservoir_step(value, 100, 1, 1, 1)
    with pytest.raises(ValueError):
        ScenarioCreate(name="nonfinite", rainfall_multiplier=value)
    with pytest.raises(ValueError):
        SectorDemand(domestic_mcm=value, agriculture_mcm=1, industrial_mcm=1, environmental_mcm=1)


def test_calendar_handles_leap_february_and_start_month() -> None:
    result = simulate_scenario(ScenarioCreate(name="calendar", start_month=date(2024, 2, 1), months=3))
    assert [point.valid_month for point in result.trajectory] == [date(2024, 2, 1), date(2024, 3, 1), date(2024, 4, 1)]
    assert result.mass_balance_error_mcm == pytest.approx(0, abs=1e-6)


def test_zero_demand_and_extreme_rainfall_spill() -> None:
    params = PilotParameters(initial_storage_mcm=100, baseline_demand_mcm=(0,) * 12)
    result = simulate_scenario(ScenarioCreate(name="wet no demand", rainfall_multiplier=3), params)
    assert result.total_unmet_mcm == 0
    assert any(point.spill_mcm > 0 for point in result.trajectory)
    assert result.final_storage_mcm <= params.reservoir_capacity_mcm


def test_conservation_is_only_demand_reduction() -> None:
    base = simulate_scenario(ScenarioCreate(name="scarcity", rainfall_multiplier=0.5))
    saved = simulate_scenario(ScenarioCreate(name="conserved", rainfall_multiplier=0.5, conservation=0.2))
    assert [point.inflow_mcm for point in base.trajectory] == [point.inflow_mcm for point in saved.trajectory]
    assert saved.total_unmet_mcm <= base.total_unmet_mcm


def test_csv_quality_and_leakage_safe_baseline() -> None:
    rows = ["month,variable,value,unit"]
    observations = []
    for index in range(36):
        value = float(index % 12 + 10)
        rows.append(f"{month(index).isoformat()},rainfall_mm,{value},mm/month")
        observations.append((month(index), value))
    result = ingest_monthly_csv(("\n".join(rows) + "\n").encode(), source_id="local-test", region_id="tn-coimbatore")
    assert result["record_count"] == 36
    assert result["verification_status"] == "user_supplied_unverified"
    evaluation = rolling_monthly_baselines(observations)
    assert evaluation["holdout_count"] == 12
    assert evaluation["models"]["seasonal_climatology"]["mae_mm"] == 0
    assert all(item["issue_month"] < item["valid_month"] for item in evaluation["predictions"])


def test_missing_month_and_duplicate_rejected() -> None:
    observations = [(month(index), 10.0) for index in range(36) if index != 14]
    with pytest.raises(ValueError, match="missing monthly"):
        rolling_monthly_baselines(observations)
    duplicate = b"month,variable,value,unit\n2024-01-01,rainfall_mm,10,mm/month\n2024-01-01,rainfall_mm,11,mm/month\n"
    with pytest.raises(ValueError, match="duplicates"):
        ingest_monthly_csv(duplicate, source_id="dup", region_id="tn-coimbatore")


def test_expired_jwt_and_role_enforcement() -> None:
    now = datetime.now(UTC)
    claims = {"sub": "expired", "roles": ["admin"], "regions": ["tn-coimbatore"], "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1), "iss": "aquasentinel", "aud": "aquasentinel-api"}
    expired = jwt.encode(claims, get_settings().jwt_secret, algorithm="HS256")
    assert client.post("/api/v1/scenarios", json={"name": "expired token"}, headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert client.post("/api/v1/alerts/rules?threshold=0.3", headers=headers("researcher")).status_code == 403


def test_api_ingestion_backtest_and_provenance_workflow() -> None:
    csv_rows = ["month,variable,value,unit"] + [f"{month(i)},rainfall_mm,{10 + i % 12},mm/month" for i in range(36)]
    csv_data = ("\n".join(csv_rows) + "\n").encode()
    uploaded = client.post("/api/v1/ingestion/monthly-csv", content=csv_data, headers={**headers(), "X-Source-ID": "local-demo-export", "X-Region-ID": "tn-coimbatore", "Content-Type": "text/csv"})
    assert uploaded.status_code == 200
    assert uploaded.json()["data"]["eligible_for_active_forecast"] is False
    assert uploaded.json()["meta"]["source_type"] == "unverified"
    assert uploaded.json()["meta"]["synthetic"] is False
    points = [{"month": month(i).isoformat(), "rainfall_mm": 10 + i % 12} for i in range(36)]
    evaluated = client.post("/api/v1/forecasts/backtest", json={"source_id": "local-demo-export", "observations": points}, headers=headers())
    assert evaluated.status_code == 200
    assert evaluated.json()["data"]["holdout_count"] == 12
    created = client.post("/api/v1/scenarios", json={"name": "deficit workflow", "rainfall_multiplier": 0.7}, headers=headers()).json()["data"]
    simulated = client.post(f"/api/v1/scenarios/{created['id']}/run", headers=headers())
    assert simulated.status_code == 200
    assert abs(simulated.json()["data"]["mass_balance_error_mcm"]) < 1e-6
    plan = client.post("/api/v1/optimizations", json={"available_water_mcm": 40, "preserve_reserve_mcm": 8, "demand": {"domestic_mcm": 10, "agriculture_mcm": 25, "industrial_mcm": 5, "environmental_mcm": 4}}, headers=headers())
    assert plan.json()["data"]["status"] == "optimal"
    advisory = client.post("/api/v1/advisories/preview", json={"region_id": "tn-coimbatore", "language": "ta"})
    assert advisory.status_code == 200
    assert client.get(f"/api/v1/provenance/{created['id']}").status_code == 200
    assert client.get("/api/v1/provenance/made-up-artifact").status_code == 404


def test_optimizer_allocation_is_nonnegative_and_bounded() -> None:
    request = OptimizationRequest(available_water_mcm=40, preserve_reserve_mcm=8, demand=SectorDemand(domestic_mcm=10, agriculture_mcm=25, industrial_mcm=5, environmental_mcm=4))
    result = optimize_allocation(request)
    assert result["status"] == "optimal"
    assert all(value >= 0 for value in result["allocation_mcm"].values())
    assert result["water_used_mcm"] <= 32
    assert result["budget_assessment"].startswith("Budget is recorded")


def test_fao56_bangkok_reference_example() -> None:
    # FAO Irrigation and Drainage Paper 56, Chapter 4, Example 17: 5.72 mm/day.
    result = penman_monteith_daily_et0(25.6, 34.8, 30.2, 14.33, 0.14, 2.0, 2.85, 101.3)
    assert result == pytest.approx(5.72, abs=0.06)
    api = client.post("/api/v1/agriculture/et0/fao56", json={
        "temp_min_c": 25.6, "temp_max_c": 34.8, "temp_mean_c": 30.2,
        "net_radiation_mj_m2_day": 14.33, "soil_heat_flux_mj_m2_day": 0.14,
        "wind_speed_2m_m_s": 2.0, "actual_vapour_pressure_kpa": 2.85,
        "atmospheric_pressure_kpa": 101.3,
    })
    assert api.status_code == 200
    assert api.json()["data"]["reference_et0_mm_day"] == pytest.approx(result)
    with pytest.raises(ValueError):
        penman_monteith_daily_et0(25, 35, 30, 14, 0, 2, 100, 101)
    with pytest.raises(ValueError):
        fao56_reference_et0(30, 20, 25, 10)


def test_enso_screening_and_teleconnection_edge_cases() -> None:
    assert classify_enso([-0.8] * 5)["phase"] == "la_nina"
    assert classify_enso([0.8, -0.8, 0, 0, 0])["phase"] == "neutral_or_transition"
    with pytest.raises(ValueError):
        classify_enso([float("nan")] * 5)
    with pytest.raises(ValueError):
        lagged_teleconnection([1, 2], [1], max_lag=1)
    constant = lagged_teleconnection([0.2] * 12, list(range(12)), max_lag=2)
    assert all(item["correlation"] is None for item in constant)
    varying = lagged_teleconnection(list(range(12)), list(range(12)), max_lag=2)
    assert varying[0]["correlation"] == pytest.approx(1)


def test_risk_rejects_impossible_fraction_and_anomaly() -> None:
    with pytest.raises(ValueError):
        drought_risk(-20, -20, 1.1, 0.5)
    with pytest.raises(ValueError):
        drought_risk(-101, -20, 0.5, 0.5)
    assert client.get("/api/v1/risks?rainfall_anomaly_pct=-101").status_code == 422


def test_invalid_month_and_csv_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        ScenarioCreate(name="invalid month", start_month=date(2024, 2, 2))
    with pytest.raises(ValueError):
        ingest_monthly_csv(b"", source_id="empty", region_id="tn-coimbatore")
    malformed = b"month,variable,value,unit\n2024-01-01,rainfall_mm,nan,mm/month\n"
    with pytest.raises(ValueError):
        ingest_monthly_csv(malformed, source_id="nan", region_id="tn-coimbatore")
    gap = b"month,variable,value,unit\n2024-01-01,rainfall_mm,1,mm/month\n2024-03-01,rainfall_mm,2,mm/month\n"
    assert len(ingest_monthly_csv(gap, source_id="gap", region_id="tn-coimbatore")["quality"]["gaps"]) == 1


def test_reservoir_and_et_parameter_bounds() -> None:
    for args in ((0, 0, 0, 0, 0), (10, 100, 0, 0, 0, 0, 110), (101, 100, 0, 0, 0)):
        with pytest.raises(ValueError):
            reservoir_step(*args)
    assert fao56_reference_et0(20, 30, 25, 18) > 0
    assert fao56_reference_et0(-25, -15, -20, 18) == 0
    with pytest.raises(ValueError):
        fao56_reference_et0(20, 30, 25, -1)
    common = (20, 30, 25, 10, 0, 2, 1, 100)
    for changed in ((20, 30, 31, 10, 0, 2, 1, 100), (-81, 30, 25, 10, 0, 2, 1, 100), (20, 30, 25, 1, 2, 2, 1, 100), (20, 30, 25, 10, 0, 2, -1, 100)):
        with pytest.raises(ValueError):
            penman_monteith_daily_et0(*changed)
    assert penman_monteith_daily_et0(*common) > 0


def test_simulator_rejects_invalid_physical_parameters() -> None:
    scenario = ScenarioCreate(name="invalid pilot")
    for params in (
        PilotParameters(catchment_km2=-1),
        PilotParameters(runoff_coefficient=1.1),
        PilotParameters(initial_storage_mcm=110),
        PilotParameters(mean_monthly_rainfall_mm=(1,) * 11),
        PilotParameters(baseline_demand_mcm=(-1,) * 12),
    ):
        with pytest.raises(ValueError):
            simulate_scenario(scenario, params)


def test_backtest_rejects_too_short_or_unsorted_series() -> None:
    with pytest.raises(ValueError):
        rolling_monthly_baselines([(month(i), 1.0) for i in range(20)])
    reversed_series = list(reversed([(month(i), 1.0) for i in range(36)]))
    with pytest.raises(ValueError):
        rolling_monthly_baselines(reversed_series)


def test_intervention_planner_respects_budget_and_no_double_counting() -> None:
    payload = InterventionPlanRequest.model_validate({
        "scenario": {"name": "dry planning", "months": 12},
        "budget_million_inr": "5.000",
        "rainfall_cases": [0.5, 0.7, 1.0],
        "options": [
            {"kind": "conservation", "intensity": 0.2, "cost_million_inr": "2.000"},
            {"kind": "leakage_reduction", "intensity": 0.3, "cost_million_inr": "3.000"},
            {"kind": "emergency_supply", "intensity": 8, "cost_million_inr": "20.000"},
        ],
    })
    result = plan_interventions(payload)
    assert result["status"] == "optimal_within_enumerated_options"
    assert float(result["cost_million_inr"]) <= 5
    assert all(item["kind"] != "emergency_supply" for item in result["selected_options"])
    assert result["planned"]["worst_case_unmet_mcm"] <= result["baseline"]["worst_case_unmet_mcm"]
    # Conservation reduces demand in the twin; it does not add a second inflow.
    baseline = simulate_scenario(ScenarioCreate(name="base", rainfall_multiplier=0.5))
    conserved = simulate_scenario(ScenarioCreate(name="saved", rainfall_multiplier=0.5, conservation=0.2))
    assert [point.inflow_mcm for point in baseline.trajectory] == [point.inflow_mcm for point in conserved.trajectory]
    api = client.post("/api/v1/optimizations/interventions", json=payload.model_dump(mode="json"), headers=headers())
    assert api.status_code == 200
    assert api.json()["data"]["rainfall_case_probabilities"] is None


def test_intervention_planner_rejects_stacked_excessive_conservation() -> None:
    with pytest.raises(ValueError):
        InterventionPlanRequest.model_validate({
            "scenario": {"name": "over limit", "conservation": 0.7},
            "budget_million_inr": 10,
            "rainfall_cases": [0.7],
            "options": [{"kind": "conservation", "intensity": 0.7, "cost_million_inr": 1}],
        })


def test_approval_monitoring_reassessment_api_cycle() -> None:
    plan_payload = {
        "scenario": {"name": "approval cycle", "months": 6},
        "budget_million_inr": "2.000",
        "rainfall_cases": [0.5, 0.8],
        "options": [{"kind": "conservation", "intensity": 0.2, "cost_million_inr": "2.000"}],
    }
    plan_response = client.post("/api/v1/optimizations/interventions", json=plan_payload, headers=headers())
    assert plan_response.status_code == 200
    plan = plan_response.json()["data"]
    proposed = client.post("/api/v1/interventions/proposals", json={
        "plan_id": plan["id"], "responsible_authority": "Pilot district water office",
        "review_by": "2026-11-01", "rationale": "Review the modeled conservation option against local measurements.",
    }, headers=headers())
    assert proposed.status_code == 201
    proposal_id = proposed.json()["data"]["id"]
    assert proposed.json()["data"]["operational_action_executed"] is False
    assert client.post(f"/api/v1/interventions/{proposal_id}/approve", headers=headers()).status_code == 403
    approval = client.post(f"/api/v1/interventions/{proposal_id}/approve", headers=headers("authority"))
    assert approval.status_code == 200
    assert approval.json()["data"]["status"] == "approved"
    recorded = client.post(f"/api/v1/interventions/{proposal_id}/action-record", json={
        "action_reference": "local-ledger-001", "recorded_at": "2026-10-08T10:00:00Z",
        "note": "Authority reports beginning leak repairs in the pilot area.",
    }, headers=headers("authority"))
    assert recorded.status_code == 200
    outcome = client.post(f"/api/v1/interventions/{proposal_id}/outcome", json={
        "observed_unmet_mcm": 10, "observation_source_id": "local-ledger-001",
        "measured_at": "2026-11-08T10:00:00Z",
    }, headers=headers("authority"))
    assert outcome.status_code == 200
    assert outcome.json()["data"]["status"] == "reassessment_due"
