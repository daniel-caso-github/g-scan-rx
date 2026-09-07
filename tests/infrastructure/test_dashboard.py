from prometheus_client import CollectorRegistry, Counter, Histogram

from src.infrastructure.observability.dashboard import render_dashboard_html


def _build_registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    verdicts = Counter("gscan_verdicts_total", "test", ["status"], registry=registry)
    requests = Counter("gscan_requests_total", "test", ["endpoint", "status_code"], registry=registry)
    abstentions = Counter("gscan_abstentions_total", "test", registry=registry)
    cost = Counter("gscan_cost_usd_total", "test", ["model"], registry=registry)
    latency = Histogram("gscan_request_duration_seconds", "test", ["endpoint"], registry=registry)

    verdicts.labels(status="verified").inc(3)
    verdicts.labels(status="not_found").inc(1)
    requests.labels(endpoint="/process", status_code="200").inc(4)
    abstentions.inc(2)
    cost.labels(model="gemini-2.0-flash").inc(0.5)
    latency.labels(endpoint="/process").observe(0.2)
    latency.labels(endpoint="/process").observe(0.4)

    return registry


def test_dashboard_shows_hallucination_rate():
    """1 not_found out of 4 total drug verdicts = 25% hallucination rate."""
    html = render_dashboard_html(registry=_build_registry())
    assert "25.0%" in html


def test_dashboard_shows_abstention_rate():
    """2 abstentions out of 4 /process requests = 50% abstention rate."""
    html = render_dashboard_html(registry=_build_registry())
    assert "50.0%" in html


def test_dashboard_shows_total_cost():
    html = render_dashboard_html(registry=_build_registry())
    assert "0.50" in html


def test_dashboard_shows_average_latency_in_ms():
    """Average of 0.2s and 0.4s observations = 300.0 ms."""
    html = render_dashboard_html(registry=_build_registry())
    assert "300.0 ms" in html


def test_dashboard_handles_empty_registry_without_crashing():
    html = render_dashboard_html(registry=CollectorRegistry())
    assert "sin datos" in html


def test_dashboard_has_no_forced_meta_refresh():
    """WCAG 2.2.1 Timing Adjustable: no full-page reload the visitor can't control."""
    html = render_dashboard_html(registry=CollectorRegistry())
    assert "http-equiv=\"refresh\"" not in html


def test_dashboard_has_pause_control_for_auto_update():
    html = render_dashboard_html(registry=CollectorRegistry())
    assert 'aria-pressed="true"' in html
