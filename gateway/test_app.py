from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_contract() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gateway"}


def test_components_contract() -> None:
    response = client.get("/components")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"ragflow", "conscious_river", "research_agent"}
    assert all(isinstance(value, str) and value.startswith("http") for value in payload.values())
