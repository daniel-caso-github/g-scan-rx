import time

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "gscan_requests_total",
    "Total HTTP requests",
    ["endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "gscan_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records per-endpoint request counts and latencies for Prometheus scraping."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        # Use the route template (e.g. /agent/{thread_id}/confirm) instead of the raw path
        # to avoid unbounded label cardinality from path parameters.
        route = request.scope.get("route")
        endpoint = route.path if route is not None else request.url.path
        REQUEST_COUNT.labels(endpoint=endpoint, status_code=str(response.status_code)).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        return response
