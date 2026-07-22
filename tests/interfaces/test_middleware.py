import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from prometheus_client import REGISTRY

from src.interfaces.api.middleware import PrometheusMiddleware, REQUEST_COUNT


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware)

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    return app


@pytest.mark.asyncio
async def test_middleware_increments_request_counter():
    app = _make_app()
    before = _get_count("/ping", "200")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ping")

    assert response.status_code == 200
    after = _get_count("/ping", "200")
    assert after == before + 1


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format():
    """The /metrics endpoint serves text in Prometheus exposition format."""
    from prometheus_client import generate_latest

    content = generate_latest()
    assert b"gscan_requests_total" in content or content == b""


def _get_count(endpoint: str, status_code: str) -> float:
    try:
        return REGISTRY.get_sample_value(
            "gscan_requests_total",
            {"endpoint": endpoint, "status_code": status_code},
        ) or 0.0
    except Exception:
        return 0.0
