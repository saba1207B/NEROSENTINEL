"""Reproducible local CPU benchmark; prints measurements, not claims."""

import json
from statistics import median
from time import perf_counter

import numpy as np
from fastapi.testclient import TestClient

from aquasentinel.engines.optimization import optimize_allocation
from aquasentinel.engines.simulation import monte_carlo, simulate_scenario
from aquasentinel.main import app
from aquasentinel.schemas import OptimizationRequest, ScenarioCreate, SectorDemand


def measured(call, repeats: int) -> dict[str, float]:
    values = []
    for _ in range(repeats):
        start = perf_counter()
        call()
        values.append((perf_counter() - start) * 1000)
    return {
        "p50_ms": round(median(values), 3),
        "p95_ms": round(float(np.percentile(values, 95)), 3),
        "p99_ms": round(float(np.percentile(values, 99)), 3),
        "runs": repeats,
    }


def main() -> None:
    scenario = ScenarioCreate(name="benchmark")
    allocation = OptimizationRequest(
        available_water_mcm=50,
        preserve_reserve_mcm=8,
        demand=SectorDemand(domestic_mcm=12, agriculture_mcm=30, industrial_mcm=8, environmental_mcm=5),
    )
    with TestClient(app) as client:
        client.get("/api/v1/health")
        results = {
            "api_health": measured(lambda: client.get("/api/v1/health"), 50),
            "api_dashboard": measured(lambda: client.get("/api/v1/dashboard/summary"), 50),
            "digital_twin_12_months": measured(lambda: simulate_scenario(scenario), 50),
            "monte_carlo_100_iterations": measured(
                lambda: monte_carlo(scenario, 100, 0.15, 0.08), 5
            ),
            "allocation_lp": measured(lambda: optimize_allocation(allocation), 20),
        }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
