from src.domain.ports.guardrail import Guardrail, GuardrailResult


class NullGuardrail(Guardrail):
    """No-op guardrail. Used when the real guardrail library is not configured."""

    async def check(self, text: str) -> GuardrailResult:
        return GuardrailResult(passed=True)
