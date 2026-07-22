from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class Tracer(ABC):
    """Port: records traces and spans for LLM calls and agent steps."""

    @abstractmethod
    def trace(
        self,
        name: str,
        input: dict,
        output: dict | None = None,
        metadata: dict | None = None,
    ) -> None: ...

    @abstractmethod
    def span(self, name: str, **kwargs) -> AbstractContextManager: ...
