import pytest
from fastapi.testclient import TestClient

from analytics_core.settings import get_settings
from bi.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    get_settings.cache_clear()
    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()
