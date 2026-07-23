from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class Tracer(ABC):
    """Port: records traces, spans, and LLM generation observations."""

    @abstractmethod
    def span(self, name: str, **kwargs) -> AbstractContextManager: ...

    @abstractmethod
    def generation(
        self,
        name: str,
        model: str,
        input: dict,
    ) -> AbstractContextManager: ...

    def flush(self) -> None:  # noqa: B027 - optional hook; no-op default is intentional
        """Optional no-op hook; tracers with buffered output may override it."""
