# Optimization validation

Status: IMPLEMENTED for bounded allocation and discrete intervention selection; PARTIAL for operational cost and infrastructure constraints.

The SciPy HiGHS allocation solver enforces available water after reserve, domestic minimum and environmental minimum, sector demand upper bounds, and nonnegative allocations. It returns infeasible when essential minimums exceed usable water. The response exposes the objective weights, binding water constraint, objective value, solver runtime and approval requirement. The legacy `budget_million_inr` input is recorded but has no cost coefficients in this LP; the result explicitly states that no cost feasibility claim is made.

The V2 intervention planner enumerates at most five declared options, applies each selected effect once, evaluates each candidate against caller supplied rainfall cases, and chooses minimum worst-case unmet demand followed by minimum declared cost. Costs use decimal arithmetic. It does not assign probabilities to hypothetical cases. A direct test verifies that conservation changes demand without adding an artificial inflow.

Neither engine controls reservoirs or public rationing. Options, costs, policy priorities, infrastructure limits and hydrological parameters require qualified authority review before real-world use.

