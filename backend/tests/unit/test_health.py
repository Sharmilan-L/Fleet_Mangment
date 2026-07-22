from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from evolvex.core.config import Settings


@pytest.mark.asyncio
async def test_liveness_endpoint(client: AsyncClient) -> None:
    """
    Verifies GET /health process liveness endpoint.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "evolvex-api"
    assert "timestamp" in data
    assert "environment" not in data


@pytest.mark.asyncio
async def test_database_health_mocked_success(client: AsyncClient) -> None:
    """
    Verifies GET /api/v1/health/database readiness endpoint when ping succeeds.
    """
    with patch("evolvex.api.health.ping_database", new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = True
        response = await client.get("/api/v1/health/database")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["status"] == "healthy"
        assert payload["data"]["database"] == "connected"
        assert "databaseType" not in payload["data"]
        assert "requestId" in payload["meta"]
        assert "timestamp" in payload["meta"]


@pytest.mark.asyncio
async def test_database_health_mocked_failure(client: AsyncClient) -> None:
    """
    Verifies GET /api/v1/health/database readiness endpoint when ping fails.
    """
    with patch("evolvex.api.health.ping_database", new_callable=AsyncMock) as mock_ping:
        mock_ping.side_effect = ConnectionError("Could not establish connection to PostgreSQL")
        response = await client.get("/api/v1/health/database")
        assert response.status_code == 503
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert payload["error"]["message"] == "Database connectivity check failed"
        assert "requestId" in payload["meta"]
        assert "timestamp" in payload["meta"]


@pytest.mark.asyncio
async def test_request_id_middleware_generated(client: AsyncClient) -> None:
    """
    Verifies RequestIDMiddleware generates X-Request-ID when client omits header.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


@pytest.mark.asyncio
async def test_request_id_middleware_preserved(client: AsyncClient) -> None:
    """
    Verifies RequestIDMiddleware preserves valid client-supplied X-Request-ID.
    """
    custom_id = "req_custom_client_12345"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_allowed_origins_parsing() -> None:
    """
    Verifies settings.ALLOWED_ORIGINS parses JSON array strings correctly into list[str].
    """
    settings_from_json = Settings(
        ALLOWED_ORIGINS='["http://localhost:5173", "http://127.0.0.1:5173"]'
    )
    assert settings_from_json.ALLOWED_ORIGINS == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    settings_from_csv = Settings(ALLOWED_ORIGINS="http://localhost:5173, http://127.0.0.1:5173")
    assert settings_from_csv.ALLOWED_ORIGINS == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
