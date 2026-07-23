import logging

from src.domain.ports.guardrail import Guardrail, GuardrailResult

logger = logging.getLogger(__name__)


class PiiGuardrail(Guardrail):
    """Detects PII in extracted text using presidio-analyzer.

    Lazy-imports presidio so the container starts even without the spacy model.
    """

    def __init__(self, language: str = "es") -> None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "es", "model_name": "es_core_news_sm"}],
        })
        self._analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["es"])
        self._language = language

    # PERSON and DATE_OF_BIRTH are expected fields on a prescription; only
    # block anomalous identifiers that signal data contamination or injection.
    _PATIENT_PII = [
        "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "IBAN_CODE",
    ]

    async def check(self, text: str) -> GuardrailResult:
        results = self._analyzer.analyze(
            text=text, language=self._language, entities=self._PATIENT_PII,
            score_threshold=0.75,
        )
        if results:
            types = {r.entity_type for r in results}
            logger.warning("PII detectado en texto extraído: %s", types)
            return GuardrailResult(passed=False, risk_type="PII")
        return GuardrailResult(passed=True)
