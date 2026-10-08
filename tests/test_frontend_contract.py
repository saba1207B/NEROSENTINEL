"""Smoke the exact public API shapes used by the attached dashboard."""

from fastapi.testclient import TestClient

from aquasentinel.main import app
from aquasentinel.security import create_access_token

client = TestClient(app)


def test_frontend_read_contracts() -> None:
    paths = (
        "/api/v1/health",
        "/api/v1/dashboard/summary",
        "/api/v1/enso/current",
        "/api/v1/enso/history",
        "/api/v1/forecasts",
        "/api/v1/reservoirs",
        "/api/v1/reservoirs/demo-reservoir-1",
        "/api/v1/reservoirs/demo-reservoir-1/forecast",
        "/api/v1/water/demand",
        "/api/v1/water/balance",
        "/api/v1/regions/tn-coimbatore",
        "/api/v1/alerts",
        "/api/v1/sources",
    )
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "data" in response.json() and "meta" in response.json(), path
    assert client.get("/api/v1/dashboard/summary").json()["meta"]["synthetic"] is True


def test_browser_cors_and_scenario_flow() -> None:
    origin = "http://127.0.0.1:3000"
    preflight = client.options(
        "/api/v1/scenarios",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"},
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == origin
    token = create_access_token("frontend-contract-test", ["researcher"], ["tn-coimbatore"])
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/scenarios", json={"name": "Frontend integration case", "months": 6}, headers=headers)
    assert created.status_code == 201
    result = client.post(f"/api/v1/scenarios/{created.json()['data']['id']}/run", json={}, headers=headers)
    assert result.status_code == 200
    assert len(result.json()["data"]["trajectory"]) == 6
    assert result.json()["meta"]["model_version"] == "digital-twin-v1"


def test_assistant_contract_is_bounded() -> None:
    response = client.post("/api/v1/assistant/query", json={"question": "Why drought risk?", "region_id": "tn-coimbatore"})
    assert response.status_code == 200
    assert response.json()["data"]["can_trigger_operations"] is False
