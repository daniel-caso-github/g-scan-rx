import logging

from src.domain.ports.guardrail import Guardrail, GuardrailResult

logger = logging.getLogger(__name__)


class PiiGuardrail(Guardrail):
    """Detects PII in extracted text using presidio-analyzer.

    Lazy-imports presidio so the container starts even without the spacy model.
    """

    def __init__(self, language: str = "es") -> None:
        from presidio_analyzer import AnalyzerEngine

        self._analyzer = AnalyzerEngine()
        self._language = language

    async def check(self, text: str) -> GuardrailResult:
        results = self._analyzer.analyze(text=text, language=self._language)
        if results:
            types = {r.entity_type for r in results}
            logger.warning("PII detectado en texto extraído: %s", types)
            return GuardrailResult(passed=False, risk_type="PII")
        return GuardrailResult(passed=True)
