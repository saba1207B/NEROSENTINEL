"""Bounded exhaustive intervention planning under declared rainfall cases."""

from itertools import combinations

from aquasentinel.engines.simulation import simulate_scenario
from aquasentinel.schemas import InterventionOption, InterventionPlanRequest, ScenarioCreate


def _apply(base: ScenarioCreate, options: tuple[InterventionOption, ...]) -> ScenarioCreate:
    parameters = base.model_dump()
    for option in options:
        if option.kind == "conservation":
            parameters["conservation"] = 1 - (1 - parameters["conservation"]) * (1 - option.intensity)
        elif option.kind == "leakage_reduction":
            parameters["leakage_reduction"] = 1 - (1 - parameters["leakage_reduction"]) * (1 - option.intensity)
        else:
            parameters["emergency_supply_mcm"] += option.intensity
    return ScenarioCreate.model_validate(parameters)


def plan_interventions(request: InterventionPlanRequest) -> dict[str, object]:
    cases = sorted(set(request.rainfall_cases))

    def evaluate(selected: tuple[InterventionOption, ...]) -> dict[str, object]:
        adjusted = _apply(request.scenario, selected)
        outcomes = []
        for rainfall in cases:
            case = adjusted.model_copy(update={"rainfall_multiplier": rainfall})
            result = simulate_scenario(case)
            outcomes.append({"rainfall_multiplier": rainfall, "total_unmet_mcm": result.total_unmet_mcm, "reliability": result.reliability, "mass_balance_error_mcm": result.mass_balance_error_mcm})
        return {"worst_case_unmet_mcm": max(item["total_unmet_mcm"] for item in outcomes), "cases": outcomes}

    baseline = evaluate(())
    candidates = []
    for count in range(len(request.options) + 1):
        for selected in combinations(request.options, count):
            cost = sum((option.cost_million_inr for option in selected), start=0)
            if cost > request.budget_million_inr:
                continue
            outcome = evaluate(selected)
            candidates.append((outcome["worst_case_unmet_mcm"], cost, selected, outcome))
    if not candidates:
        raise ArithmeticError("baseline intervention candidate is missing")
    best = min(candidates, key=lambda item: (item[0], item[1]))
    return {
        "status": "optimal_within_enumerated_options",
        "objective": "lexicographic: minimize worst-case unmet demand, then supplied cost",
        "selected_options": [option.model_dump(mode="json") for option in best[2]],
        "cost_million_inr": str(best[1]),
        "budget_million_inr": str(request.budget_million_inr),
        "baseline": baseline,
        "planned": best[3],
        "worst_case_shortage_reduction_mcm": round(baseline["worst_case_unmet_mcm"] - best[3]["worst_case_unmet_mcm"], 4),
        "evaluated_candidates": len(candidates),
        "rainfall_case_probabilities": None,
        "requires_human_approval": True,
        "limitations": ["Costs and intervention intensities are user supplied, not calibrated.", "Only supplied discrete options and rainfall cases were searched.", "Operational releases or rationing are not automated."],
    }
