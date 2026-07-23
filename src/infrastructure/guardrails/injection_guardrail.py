import logging

from src.domain.ports.guardrail import Guardrail, GuardrailResult

logger = logging.getLogger(__name__)


class InjectionGuardrail(Guardrail):
    """Detects prompt injection in extracted text using llm-guard.

    Lazy-imports llm_guard so the container starts even without the model.
    """

    def __init__(self) -> None:
        from llm_guard.input_scanners import PromptInjection

        self._scanner = PromptInjection()

    async def check(self, text: str) -> GuardrailResult:
        _sanitized, is_valid, risk_score = self._scanner.scan(prompt=text)
        if not is_valid:
            logger.warning("Prompt injection detectado, risk_score=%.3f", risk_score)
            return GuardrailResult(passed=False, risk_type="PROMPT_INJECTION")
        return GuardrailResult(passed=True)
