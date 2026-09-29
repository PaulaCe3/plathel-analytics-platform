from fastapi.testclient import TestClient

from analytics_core.errors import AppError
from bi.api.routers import health


def test_app_error_uses_standard_envelope(client: TestClient, monkeypatch) -> None:
    def controlled_failure() -> dict[str, str]:
        raise AppError(
            code="CONTROLLED_TEST_ERROR",
            http_status=422,
            message="No se pudo completar la operación.",
            details=[{"field": "sample"}],
        )

    monkeypatch.setattr(health.system_service, "health_status", controlled_failure)
    response = client.get("/api/v1/health", headers={"X-Request-ID": "controlled-1"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "CONTROLLED_TEST_ERROR",
            "message": "No se pudo completar la operación.",
            "details": [{"field": "sample"}],
            "request_id": "controlled-1",
        }
    }


def test_unexpected_error_hides_technical_details(client: TestClient, monkeypatch) -> None:
    def unexpected_failure() -> dict[str, str]:
        raise ValueError("sensitive internal path C:/private/customer.csv")

    monkeypatch.setattr(health.system_service, "health_status", unexpected_failure)
    response = client.get("/api/v1/health", headers={"X-Request-ID": "unexpected-1"})
    body = response.json()

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "unexpected-1"
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["details"] == []
    assert body["error"]["request_id"] == "unexpected-1"
    assert "ValueError" not in response.text
    assert "traceback" not in response.text.lower()
    assert "customer.csv" not in response.text
