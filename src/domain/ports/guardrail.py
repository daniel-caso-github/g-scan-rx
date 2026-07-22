from abc import ABC, abstractmethod

from pydantic import BaseModel


class GuardrailResult(BaseModel):
    passed: bool
    risk_type: str | None = None


class Guardrail(ABC):
    """Port: checks a text string for security risks (PII, prompt injection, etc.)."""

    @abstractmethod
    async def check(self, text: str) -> GuardrailResult: ...
