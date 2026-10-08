from fastapi.testclient import TestClient

from aquasentinel.main import app
from aquasentinel.security import create_access_token

client = TestClient(app)


def auth_headers(role: str = "researcher", region: str = "tn-coimbatore") -> dict[str, str]:
    token = create_access_token("api-test-user", [role], [region])
    return {"Authorization": f"Bearer {token}"}


def test_health_contract() -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "test-correlation"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-correlation"
    body = response.json()
    assert set(body) == {"data", "meta"}
    assert body["meta"]["source_type"] == "modeled"


def test_scenario_end_to_end() -> None:
    created = client.post("/api/v1/scenarios", json={"name": "API drought case", "rainfall_multiplier": 0.65, "months": 12}, headers=auth_headers())
    assert created.status_code == 201
    scenario_id = created.json()["data"]["id"]
    run = client.post(f"/api/v1/scenarios/{scenario_id}/run", headers=auth_headers())
    assert run.status_code == 200
    assert len(run.json()["data"]["trajectory"]) == 12
    result = client.get(f"/api/v1/scenarios/{scenario_id}/results", headers=auth_headers())
    assert result.status_code == 200
    assert abs(result.json()["data"]["mass_balance_error_mcm"]) < 1e-6


def test_compare_rejects_more_than_four() -> None:
    payload = [{"name": f"scenario {i}"} for i in range(5)]
    response = client.post("/api/v1/scenarios/compare", json=payload, headers=auth_headers())
    assert response.status_code == 422


def test_optimization_reports_human_approval() -> None:
    response = client.post("/api/v1/optimizations", json={"available_water_mcm": 50, "preserve_reserve_mcm": 8, "demand": {"domestic_mcm": 12, "agriculture_mcm": 30, "industrial_mcm": 8, "environmental_mcm": 5}}, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["data"]["requires_human_approval"] is True


def test_unknown_region_is_404() -> None:
    assert client.get("/api/v1/regions/made-up").status_code == 404


def test_openapi_has_required_families() -> None:
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema["paths"]
    for expected in ("/api/v1/regions", "/api/v1/enso/current", "/api/v1/risks", "/api/v1/scenarios", "/api/v1/optimizations", "/api/v1/provenance/{artifact_id}", "/api/v1/health"):
        assert expected in paths


def test_validation_error_is_standardized() -> None:
    response = client.post("/api/v1/scenarios", json={"name": "x", "rainfall_multiplier": -1}, headers=auth_headers())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_static_scenario_routes_are_reachable() -> None:
    cases = [{"name": "baseline"}, {"name": "conserved", "conservation": 0.2}]
    comparison = client.post("/api/v1/scenarios/compare", json=cases, headers=auth_headers())
    assert comparison.status_code == 200
    assert len(comparison.json()["data"]["items"]) == 2
    uncertainty = client.post("/api/v1/scenarios/monte-carlo", json={"scenario": cases[0], "iterations": 20}, headers=auth_headers())
    assert uncertainty.status_code == 200
    assert uncertainty.json()["data"]["iterations"] == 20


def test_mutations_require_valid_region_scoped_role() -> None:
    payload = {"name": "Permission test"}
    assert client.post("/api/v1/scenarios", json=payload).status_code == 401
    assert client.post("/api/v1/scenarios", json=payload, headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.post("/api/v1/scenarios", json=payload, headers=auth_headers("viewer")).status_code == 403
    assert client.post("/api/v1/scenarios", json=payload, headers=auth_headers("researcher", "another-region")).status_code == 403


def test_idempotency_is_actor_scoped_and_checks_payload() -> None:
    headers = {**auth_headers(), "Idempotency-Key": "test-key-unique-1"}
    first = client.post("/api/v1/scenarios", json={"name": "Idempotent case"}, headers=headers)
    again = client.post("/api/v1/scenarios", json={"name": "Idempotent case"}, headers=headers)
    conflict = client.post("/api/v1/scenarios", json={"name": "Different case"}, headers=headers)
    assert first.status_code == 201
    assert again.json()["data"]["id"] == first.json()["data"]["id"]
    assert conflict.status_code == 409
