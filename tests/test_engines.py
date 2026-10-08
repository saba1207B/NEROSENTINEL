import math

import pytest

from aquasentinel.engines.enso import classify_enso
from aquasentinel.engines.optimization import optimize_allocation
from aquasentinel.engines.risk import drought_risk
from aquasentinel.engines.simulation import monte_carlo, simulate_scenario
from aquasentinel.engines.water import reservoir_step
from aquasentinel.schemas import OptimizationRequest, ScenarioCreate, SectorDemand


def test_reservoir_mass_balance_and_capacity() -> None:
    step = reservoir_step(90, 100, 30, 10, 2, 1, 5)
    assert step.storage_mcm == 100
    assert step.spill_mcm == 7
    assert step.release_mcm == 10
    assert abs(step.mass_balance_error_mcm) < 1e-9


def test_reservoir_never_releases_dead_storage() -> None:
    step = reservoir_step(9, 100, 0, 20, 0, dead_storage_mcm=8)
    assert step.release_mcm == 1
    assert step.storage_mcm == 8


@pytest.mark.parametrize("invalid", [-1, -10])
def test_reservoir_rejects_negative_input(invalid: float) -> None:
    with pytest.raises(ValueError):
        reservoir_step(20, 100, invalid, 2, 1)


def test_scenario_is_reproducible_and_conserves_mass() -> None:
    scenario = ScenarioCreate(name="test baseline", months=24, rainfall_multiplier=0.8)
    first, second = simulate_scenario(scenario), simulate_scenario(scenario)
    assert first.trajectory == second.trajectory
    assert math.isclose(first.mass_balance_error_mcm, 0, abs_tol=1e-6)
    assert all(0 <= point.storage_mcm <= 105 for point in first.trajectory)
    assert all(0 <= point.groundwater_index <= 1 for point in first.trajectory)


def test_conservation_intervention_cannot_increase_deficit() -> None:
    baseline = simulate_scenario(ScenarioCreate(name="baseline", rainfall_multiplier=0.65))
    conserved = simulate_scenario(ScenarioCreate(name="conserved", rainfall_multiplier=0.65, conservation=0.2, leakage_reduction=0.3))
    assert conserved.total_unmet_mcm <= baseline.total_unmet_mcm


def test_monte_carlo_seed_is_reproducible() -> None:
    scenario = ScenarioCreate(name="uncertainty", seed=7)
    first = monte_carlo(scenario, 25, 0.1, 0.05)
    second = monte_carlo(scenario, 25, 0.1, 0.05)
    assert first == second


def test_optimizer_respects_physical_and_minimum_constraints() -> None:
    request = OptimizationRequest(available_water_mcm=50, preserve_reserve_mcm=8, demand=SectorDemand(domestic_mcm=12, agriculture_mcm=30, industrial_mcm=8, environmental_mcm=5))
    result = optimize_allocation(request)
    assert result["status"] == "optimal"
    assert result["water_used_mcm"] <= 42
    assert result["allocation_mcm"]["domestic"] >= 10.8
    assert result["allocation_mcm"]["environmental"] >= 3
    assert result["requires_human_approval"] is True


def test_optimizer_reports_infeasible_minimums() -> None:
    request = OptimizationRequest(available_water_mcm=20, preserve_reserve_mcm=5, demand=SectorDemand(domestic_mcm=20, agriculture_mcm=3, industrial_mcm=2, environmental_mcm=5))
    result = optimize_allocation(request)
    assert result["status"] == "infeasible"
    assert result["alternatives"]


def test_enso_requires_five_seasons() -> None:
    assert classify_enso([0.8] * 4)["phase"] == "insufficient_data"
    assert classify_enso([0.8] * 5)["phase"] == "el_nino"


def test_risk_is_explicit_screening_not_probability() -> None:
    result = drought_risk(-30, -20, 0.4, 0.5)
    assert sum(result["weights"].values()) == pytest.approx(1)
    assert "not a calibrated" in result["uncertainty"]

