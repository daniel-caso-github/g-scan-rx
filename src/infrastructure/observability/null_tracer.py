from contextlib import contextmanager, nullcontext

from src.domain.ports.tracer import Tracer


class _NullObs:
    def update(self, **_) -> None:
        pass


class NullTracer(Tracer):
    """No-op tracer. Used when Langfuse is not configured."""

    def span(self, name: str, **kwargs):
        return nullcontext()

    @contextmanager
    def generation(self, name: str, model: str, input: dict):
        yield _NullObs()
