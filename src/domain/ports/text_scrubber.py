from abc import ABC, abstractmethod


class TextScrubber(ABC):
    """Port: removes / anonymizes PII from free text before it leaves the system.

    Used to sanitize model input/output before it is sent to external
    observability backends (e.g. Langfuse traces), which may otherwise leak
    patient PII.
    """

    @abstractmethod
    def scrub(self, text: str) -> str:
        """Return a copy of `text` with PII anonymized. Must never raise."""
        ...
