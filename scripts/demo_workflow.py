"""Executable synthetic judge flow through the public API contract."""

import json
from datetime import date

from fastapi.testclient import TestClient

from aquasentinel.main import app
from aquasentinel.security import create_access_token


def checked(response):
    if response.status_code >= 400:
        raise RuntimeError(f"demo API step failed: {response.status_code} {response.text}")
    return response.json()


def main() -> None:
    researcher = {"Authorization": f"Bearer {create_access_token('demo-researcher', ['researcher'], ['tn-coimbatore'])}"}
    authority = {"Authorization": f"Bearer {create_access_token('demo-authority', ['authority'], ['tn-coimbatore'])}"}
    points = []
    rows = ["month,variable,value,unit"]
    for index in range(36):
        month = date(2020 + index // 12, index % 12 + 1, 1)
        rainfall = 12 + index % 12
        points.append({"month": month.isoformat(), "rainfall_mm": rainfall})
        rows.append(f"{month.isoformat()},rainfall_mm,{rainfall},mm/month")
    with TestClient(app) as client:
        uploaded = checked(client.post(
            "/api/v1/ingestion/monthly-csv",
            content=("\n".join(rows) + "\n").encode(),
            headers={**researcher, "X-Source-ID": "judge-synthetic-series", "X-Region-ID": "tn-coimbatore", "X-Synthetic-Data": "true", "Content-Type": "text/csv"},
        ))
        backtest = checked(client.post("/api/v1/forecasts/backtest", json={"source_id": "judge-synthetic-series", "synthetic": True, "observations": points}, headers=researcher))
        risk = checked(client.get("/api/v1/risks"))
        baseline = checked(client.post("/api/v1/scenarios", json={"name": "synthetic deficit", "rainfall_multiplier": 0.7, "demand_growth": 0.08}, headers=researcher))["data"]
        base_result = checked(client.post(f"/api/v1/scenarios/{baseline['id']}/run", headers=researcher))["data"]
        plan = checked(client.post("/api/v1/optimizations/interventions", json={
            "scenario": {"name": "synthetic deficit", "rainfall_multiplier": 0.7, "demand_growth": 0.08},
            "budget_million_inr": "5.000",
            "rainfall_cases": [0.5, 0.7, 1.0],
            "options": [
                {"kind": "conservation", "intensity": 0.18, "cost_million_inr": "2.000"},
                {"kind": "leakage_reduction", "intensity": 0.35, "cost_million_inr": "3.000"},
            ],
        }, headers=researcher))["data"]
        selected = {item["kind"]: item["intensity"] for item in plan["selected_options"]}
        improved = checked(client.post("/api/v1/scenarios", json={"name": "synthetic intervention", "rainfall_multiplier": 0.7, "demand_growth": 0.08, "conservation": selected.get("conservation", 0), "leakage_reduction": selected.get("leakage_reduction", 0)}, headers=researcher))["data"]
        improved_result = checked(client.post(f"/api/v1/scenarios/{improved['id']}/run", headers=researcher))["data"]
        proposed = checked(client.post("/api/v1/interventions/proposals", json={"plan_id": plan["id"], "responsible_authority": "Synthetic pilot authority", "review_by": "2026-11-01", "rationale": "Review modeled conservation and leakage assumptions before any real action."}, headers=researcher))["data"]
        approved = checked(client.post(f"/api/v1/interventions/{proposed['id']}/approve", headers=authority))["data"]
        checked(client.post(f"/api/v1/interventions/{proposed['id']}/action-record", json={"action_reference": "synthetic-demo-action", "recorded_at": "2026-10-08T10:00:00Z", "note": "Synthetic action record; no operation was performed."}, headers=authority))
        outcome = checked(client.post(f"/api/v1/interventions/{proposed['id']}/outcome", json={"observed_unmet_mcm": improved_result["total_unmet_mcm"], "observation_source_id": "synthetic-demo-outcome", "measured_at": "2026-11-08T10:00:00Z", "synthetic": True}, headers=authority))["data"]
        provenance = checked(client.get(f"/api/v1/provenance/{baseline['id']}"))["data"]
        advisory = checked(client.post("/api/v1/advisories/preview", json={"region_id": "tn-coimbatore", "language": "ta"}))["data"]
    print(json.dumps({
        "data_status": uploaded["data"]["verification_status"],
        "backtest_status": backtest["data"]["activation_status"],
        "risk_kind": risk["data"]["items"][0]["hazard_type"],
        "baseline_unmet_mcm": base_result["total_unmet_mcm"],
        "intervention_unmet_mcm": improved_result["total_unmet_mcm"],
        "baseline_mass_residual_mcm": base_result["mass_balance_error_mcm"],
        "intervention_mass_residual_mcm": improved_result["mass_balance_error_mcm"],
        "plan_status": plan["status"],
        "plan_requires_human_approval": plan["requires_human_approval"],
        "approval_status": approved["status"],
        "outcome_status": outcome["status"],
        "provenance_artifact_id": provenance["artifact_id"],
        "advisory_language": "ta" if advisory["title"] else None,
        "operational_action_executed_by_backend": False,
    }, indent=2))


if __name__ == "__main__":
    main()
