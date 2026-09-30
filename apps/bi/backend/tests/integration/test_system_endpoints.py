from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meta_comes_from_settings(client: TestClient) -> None:
    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    assert response.json() == {
        "max_file_mb": 20,
        "max_rows": 250_000,
        "max_columns": 200,
        "ttl_minutes": 60,
        "absolute_ttl_minutes": 240,
        "preview_rows": 50,
        "allowed_extensions": [".csv", ".xlsx"],
        "default_locale": "es-AR",
        "languages": ["es"],
    }


def test_request_id_is_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "test-request-123"})

    assert response.headers["X-Request-ID"] == "test-request-123"
