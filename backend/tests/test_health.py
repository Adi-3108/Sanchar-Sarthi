from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_database_status():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "eventflow-ai-backend"
    assert payload["database"] in {"connected", "unavailable"}
    assert "database_detail" in payload
    assert payload["models"]["priority"] in {"not_loaded", "dependency_missing", "loaded"}
