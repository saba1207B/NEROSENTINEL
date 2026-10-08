from time import perf_counter

import numpy as np
from scipy.optimize import linprog

from aquasentinel.schemas import OptimizationRequest

SECTORS = ("domestic", "agriculture", "industrial", "environmental")


def optimize_allocation(request: OptimizationRequest) -> dict[str, object]:
    started = perf_counter()
    demand = np.array([
        request.demand.domestic_mcm,
        request.demand.agriculture_mcm,
        request.demand.industrial_mcm,
        request.demand.environmental_mcm,
    ])
    usable = request.available_water_mcm - request.preserve_reserve_mcm
    minimum = np.array([
        demand[0] * request.minimum_domestic_fraction,
        0.0,
        0.0,
        demand[3] * request.minimum_environmental_fraction,
    ])
    if minimum.sum() > usable:
        return {
            "status": "infeasible",
            "reason": "Essential minimum allocations exceed usable water after reserve preservation.",
            "minimum_required_mcm": round(float(minimum.sum()), 4),
            "usable_water_mcm": round(usable, 4),
            "alternatives": ["Reduce the reserve only after authority review", "Add emergency supply", "Revise minimum allocations through an authorized policy process"],
            "requires_human_approval": True,
            "runtime_ms": round((perf_counter() - started) * 1000, 3),
        }
    # Maximize weighted benefit by minimizing negative utility. Essential and environmental uses rank highest.
    priority = np.array([10.0, 3.0, 4.0, 8.0])
    solution = linprog(-priority, A_ub=np.ones((1, 4)), b_ub=[usable], bounds=list(zip(minimum, demand, strict=True)), method="highs")
    if not solution.success:
        return {"status": "infeasible", "reason": solution.message, "alternatives": ["Review physical constraints and demand assumptions"], "requires_human_approval": True, "runtime_ms": round((perf_counter() - started) * 1000, 3)}
    allocation = {sector: round(float(value), 4) for sector, value in zip(SECTORS, solution.x, strict=True)}
    unmet = {sector: round(float(wanted - value), 4) for sector, wanted, value in zip(SECTORS, demand, solution.x, strict=True)}
    return {
        "status": "optimal",
        "solver": "SciPy HiGHS linear programming",
        "allocation_mcm": allocation,
        "unmet_mcm": unmet,
        "reserve_preserved_mcm": request.preserve_reserve_mcm,
        "water_used_mcm": round(float(solution.x.sum()), 4),
        "objective_value_weighted_mcm": round(float(-solution.fun), 4),
        "objective_weights": dict(zip(SECTORS, priority.tolist(), strict=True)),
        "binding_water_constraint": bool(abs(solution.x.sum() - usable) <= 1e-8),
        "optimality_gap": 0.0,
        "runtime_ms": round((perf_counter() - started) * 1000, 3),
        "budget_assessment": "Budget is recorded but has no cost coefficients or expenditure variables; no cost feasibility claim is made.",
        "constraint_satisfaction": {"physical_availability": bool(solution.x.sum() <= usable + 1e-8), "domestic_minimum": bool(solution.x[0] + 1e-8 >= minimum[0]), "environmental_minimum": bool(solution.x[3] + 1e-8 >= minimum[3])},
        "trade_off": "Linear priority weights favor essential domestic and environmental allocations; they are explicit policy assumptions, not learned preferences.",
        "requires_human_approval": True,
    }
