import json

from aquasentinel.engines.optimization import optimize_allocation
from aquasentinel.engines.simulation import simulate_scenario
from aquasentinel.schemas import OptimizationRequest, ScenarioCreate, SectorDemand


def main() -> None:
    baseline = ScenarioCreate(name="El Nino-associated deficit demo", rainfall_multiplier=0.7, demand_growth=0.08)
    intervention = baseline.model_copy(update={"name": "Conservation and emergency supply", "conservation": 0.18, "leakage_reduction": 0.35, "emergency_supply_mcm": 18})
    before, after = simulate_scenario(baseline), simulate_scenario(intervention)
    plan = optimize_allocation(OptimizationRequest(available_water_mcm=45, preserve_reserve_mcm=8, demand=SectorDemand(domestic_mcm=12, agriculture_mcm=28, industrial_mcm=6, environmental_mcm=5)))
    print(json.dumps({"status": "synthetic_offline_demo", "baseline": {"unmet_mcm": before.total_unmet_mcm, "reliability": before.reliability}, "intervention": {"unmet_mcm": after.total_unmet_mcm, "reliability": after.reliability}, "allocation_plan": plan, "approval": "required"}, indent=2))


if __name__ == "__main__":
    main()

