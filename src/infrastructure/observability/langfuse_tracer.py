import logging
from contextlib import contextmanager

from src.domain.ports.tracer import Tracer

logger = logging.getLogger(__name__)


class LangfuseTracer(Tracer):
    """Tracer backed by Langfuse for LLM call tracing and cost tracking.

    Lazy-imports langfuse so the container starts without Langfuse credentials.
    """

    def __init__(self, public_key: str, secret_key: str, host: str) -> None:
        from langfuse import Langfuse

        self._lf = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    def trace(
        self,
        name: str,
        input: dict,
        output: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            self._lf.trace(name=name, input=input, output=output or {}, metadata=metadata or {})
        except Exception:
            logger.exception("Error enviando traza a Langfuse: name=%s", name)

    @contextmanager
    def span(self, name: str, **kwargs):
        span = None
        try:
            span = self._lf.span(name=name, **kwargs)
            yield span
        except Exception:
            logger.exception("Error creando span Langfuse: name=%s", name)
            yield None
        finally:
            if span is not None:
                try:
                    span.end()
                except Exception:
                    pass
