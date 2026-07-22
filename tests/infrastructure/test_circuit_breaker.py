import time

import pytest

from src.infrastructure.observability.circuit_breaker import CircuitBreaker, CircuitState


def test_initial_state_is_closed():
    cb = CircuitBreaker(fail_max=3, reset_timeout=60.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_opens_after_fail_max_failures():
    cb = CircuitBreaker(fail_max=3, reset_timeout=60.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False


def test_success_resets_to_closed():
    cb = CircuitBreaker(fail_max=3, reset_timeout=60.0)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_half_open_after_reset_timeout(monkeypatch):
    cb = CircuitBreaker(fail_max=1, reset_timeout=1.0)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    frozen = time.monotonic() + 2.0
    monkeypatch.setattr(
        "src.infrastructure.observability.circuit_breaker.time.monotonic",
        lambda: frozen,
    )
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.allow_request() is True
