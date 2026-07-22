import logging
from contextlib import contextmanager

from src.domain.ports.tracer import Tracer
from src.infrastructure.observability.null_tracer import _NullObs

logger = logging.getLogger(__name__)


class LangfuseTracer(Tracer):
    """Tracer backed by Langfuse v4 SDK.

    Uses get_client() singleton; credentials are passed via env vars.
    Lazy-imports langfuse so the container starts without Langfuse credentials.
    """

    def __init__(self, public_key: str, secret_key: str, host: str) -> None:
        import os
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", secret_key)
        os.environ.setdefault("LANGFUSE_HOST", host)
        from langfuse import get_client
        self._lf = get_client()

    @contextmanager
    def span(self, name: str, **kwargs):
        try:
            with self._lf.start_as_current_observation(
                as_type="span",
                name=name,
                **kwargs,
            ) as obs:
                yield obs
        except Exception:
            logger.exception("Error creando span Langfuse: name=%s", name)
            yield None

    @contextmanager
    def generation(self, name: str, model: str, input: dict):
        try:
            with self._lf.start_as_current_observation(
                as_type="generation",
                name=name,
                model=model,
                input=input,
            ) as obs:
                yield obs
        except Exception:
            logger.exception("Error creando generation Langfuse: name=%s", name)
            yield _NullObs()

    def flush(self) -> None:
        try:
            self._lf.flush()
        except Exception:
            logger.exception("Error en Langfuse flush")
