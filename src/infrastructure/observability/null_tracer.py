from contextlib import nullcontext

from src.domain.ports.tracer import Tracer


class NullTracer(Tracer):
    """No-op tracer. Used when Langfuse is not configured."""

    def trace(self, name, input, output=None, metadata=None) -> None:
        pass

    def span(self, name, **kwargs):
        return nullcontext()
