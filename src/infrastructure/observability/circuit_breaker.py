import logging
import threading
import time
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a circuit breaker rejects a call because it is OPEN."""


class CircuitBreaker:
    """Thread-safe circuit breaker with CLOSED → OPEN → HALF_OPEN states.

    Transitions:
      CLOSED  — normal; failures accumulate.
      OPEN    — after fail_max failures; all calls rejected for reset_timeout seconds.
      HALF_OPEN — after reset_timeout; one probe call allowed; success → CLOSED, failure → OPEN.
    """

    def __init__(self, fail_max: int = 5, reset_timeout: float = 60.0, name: str = "unknown") -> None:
        self.name = name
        self._fail_max = fail_max
        self._reset_timeout = reset_timeout
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._opened_at is None:
                return CircuitState.CLOSED
            if time.monotonic() - self._opened_at >= self._reset_timeout:
                return CircuitState.HALF_OPEN
            return CircuitState.OPEN

    def allow_request(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self._fail_max:
                if self._opened_at is None:
                    logger.error("circuit_breaker=%s OPEN tras %d fallos consecutivos", self.name, self._failures)
                self._opened_at = time.monotonic()
