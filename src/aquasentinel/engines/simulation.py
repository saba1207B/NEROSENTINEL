from dataclasses import dataclass
from datetime import date
from uuid import uuid4

import numpy as np

from aquasentinel.engines.water import reservoir_step
from aquasentinel.schemas import MonthlyResult, ScenarioCreate, ScenarioResult
from aquasentinel.units import M2_PER_KM2, finite, m3_to_mcm, rainfall_volume_m3


@dataclass(frozen=True)
class PilotParameters:
    initial_storage_mcm: float = 78.0
    reservoir_capacity_mcm: float = 105.0
    dead_storage_mcm: float = 8.0
    initial_groundwater_index: float = 0.54
    mean_monthly_rainfall_mm: tuple[float, ...] = (18, 15, 22, 52, 68, 44, 38, 32, 86, 178, 142, 55)
    baseline_demand_mcm: tuple[float, ...] = (15, 15, 16, 17, 18, 19, 18, 18, 17, 16, 15, 15)
    catchment_km2: float = 420.0
    runoff_coefficient: float = 0.16
    monthly_evaporation_mcm: float = 1.2
    leakage_fraction: float = 0.18


def simulate_scenario(scenario: ScenarioCreate, params: PilotParameters | None = None) -> ScenarioResult:
    p = params or PilotParameters()
    for name in ("initial_storage_mcm", "reservoir_capacity_mcm", "dead_storage_mcm", "catchment_km2", "runoff_coefficient", "monthly_evaporation_mcm", "leakage_fraction"):
        finite(getattr(p, name), name, minimum=0)
    if not 0 <= p.runoff_coefficient <= 1 or not 0 <= p.leakage_fraction < 1:
        raise ValueError("runoff and leakage fractions must be within physical bounds")
    if not 0 <= p.dead_storage_mcm <= p.initial_storage_mcm <= p.reservoir_capacity_mcm:
        raise ValueError("reservoir initial, dead and capacity storage are inconsistent")
    if len(p.mean_monthly_rainfall_mm) != 12 or len(p.baseline_demand_mcm) != 12:
        raise ValueError("monthly pilot profiles must contain twelve values")
    for value in (*p.mean_monthly_rainfall_mm, *p.baseline_demand_mcm):
        finite(value, "monthly_profile", minimum=0)
    storage, groundwater = p.initial_storage_mcm, p.initial_groundwater_index
    trajectory: list[MonthlyResult] = []
    total_in, total_out = storage, 0.0
    satisfied_months = 0
    shortage_onset = None
    violations = []
    for index in range(scenario.months):
        calendar_month = (scenario.start_month.month - 1 + index) % 12 + 1
        calendar_year = scenario.start_month.year + (scenario.start_month.month - 1 + index) // 12
        valid_month = date(calendar_year, calendar_month, 1)
        seasonal = calendar_month - 1
        rain_mm = p.mean_monthly_rainfall_mm[seasonal] * scenario.rainfall_multiplier
        incident_m3 = rainfall_volume_m3(rain_mm, p.catchment_km2 * M2_PER_KM2)
        inflow = m3_to_mcm(incident_m3 * p.runoff_coefficient)
        recharge = min(0.05, rain_mm / 2500)
        pumping_effect = 0.025 * (1 - scenario.pumping_restriction)
        groundwater = float(np.clip(groundwater + recharge - pumping_effect, 0, 1))
        base_demand = p.baseline_demand_mcm[seasonal] * ((1 + scenario.demand_growth) ** (index / 12))
        heat_factor = 1 + max(0, scenario.temperature_delta_c) * 0.015
        demand = base_demand * heat_factor * (1 - scenario.conservation)
        leakage = p.leakage_fraction * (1 - scenario.leakage_reduction)
        requested_release = demand / max(0.01, 1 - leakage)
        evaporation = p.monthly_evaporation_mcm * (1 + scenario.temperature_delta_c * 0.04)
        emergency = scenario.emergency_supply_mcm / scenario.months
        step = reservoir_step(storage, p.reservoir_capacity_mcm, inflow + emergency, requested_release, max(0, evaporation), dead_storage_mcm=p.dead_storage_mcm)
        delivered = step.release_mcm * (1 - leakage)
        conveyance_loss = step.release_mcm - delivered
        unmet = max(0.0, demand - delivered)
        if unmet > demand * 0.02 and shortage_onset is None:
            shortage_onset = index + 1
        if unmet <= demand * 0.02:
            satisfied_months += 1
        total_in += inflow + emergency
        total_out += delivered + conveyance_loss + step.evaporation_mcm + step.other_losses_mcm + step.spill_mcm
        storage = step.storage_mcm
        if step.evaporation_shortfall_mcm > 1e-9:
            violations.append(f"month {index + 1}: requested evaporation exceeded available water")
        trajectory.append(MonthlyResult(month=index + 1, valid_month=valid_month, storage_mcm=round(storage, 4), groundwater_index=round(groundwater, 4), supply_mcm=round(delivered, 4), demand_mcm=round(demand, 4), unmet_mcm=round(unmet, 4), spill_mcm=round(step.spill_mcm, 4), inflow_mcm=round(inflow + emergency, 4), evaporation_mcm=round(step.evaporation_mcm, 4), gross_release_mcm=round(step.release_mcm, 4), conveyance_loss_mcm=round(conveyance_loss, 4), mass_balance_residual_mcm=step.mass_balance_error_mcm))
    mass_error = total_in - total_out - storage
    if abs(mass_error) > 1e-6 * max(1.0, total_in):
        raise ArithmeticError("scenario mass balance violated")
    return ScenarioResult(
        scenario_id=uuid4(),
        region_id=scenario.region_id,
        trajectory=trajectory,
        total_unmet_mcm=round(sum(item.unmet_mcm for item in trajectory), 4),
        reliability=round(satisfied_months / scenario.months, 4),
        mass_balance_error_mcm=round(mass_error, 7),
        initial_storage_mcm=p.initial_storage_mcm,
        final_storage_mcm=round(storage, 4),
        shortage_onset_month=shortage_onset,
        physical_constraint_violations=violations,
        assumptions=[
            "Synthetic Tamil Nadu pilot; values are not observations.",
            "Lumped monthly rainfall-runoff model with a constant runoff coefficient.",
            "Groundwater index is dimensionless and is not groundwater volume.",
            "Reservoir releases are decision-support calculations, not operating instructions.",
        ],
    )


def monte_carlo(scenario: ScenarioCreate, iterations: int, rain_std: float, demand_std: float) -> dict[str, object]:
    rng = np.random.default_rng(scenario.seed)
    end_storage, deficits, reliabilities = [], [], []
    for _ in range(iterations):
        rain_factor = max(0.0, rng.normal(scenario.rainfall_multiplier, rain_std))
        demand_growth = max(-0.5, rng.normal(scenario.demand_growth, demand_std))
        result = simulate_scenario(scenario.model_copy(update={"rainfall_multiplier": rain_factor, "demand_growth": demand_growth}))
        end_storage.append(result.trajectory[-1].storage_mcm)
        deficits.append(result.total_unmet_mcm)
        reliabilities.append(result.reliability)
    return {
        "iterations": iterations,
        "seed": scenario.seed,
        "end_storage_mcm": _percentiles(end_storage),
        "total_unmet_mcm": _percentiles(deficits),
        "reliability": _percentiles(reliabilities),
        "probability_note": "Empirical frequencies reflect the stated input distributions, not probabilities assigned to a named climate scenario.",
    }


def _percentiles(values: list[float]) -> dict[str, float]:
    p = np.percentile(values, [5, 50, 95])
    return {"p05": round(float(p[0]), 4), "p50": round(float(p[1]), 4), "p95": round(float(p[2]), 4)}
