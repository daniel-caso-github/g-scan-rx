import logging

from src.domain.ports.text_scrubber import TextScrubber

logger = logging.getLogger(__name__)

# Entities anonymized before text reaches external observability backends.
# Broader than the blocking guardrail: here we *redact* rather than reject, so
# it is safe to also scrub PERSON / LOCATION / DATE that may identify a patient.
_SCRUB_ENTITIES = [
    "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD",
    "IBAN_CODE", "LOCATION", "DATE_TIME", "IP_ADDRESS",
]


class PresidioTextScrubber(TextScrubber):
    """Anonymizes PII in text using presidio before it is traced.

    Lazy-imports presidio so the container starts even without the spacy model.
    Never raises: returning the original text on failure would be unsafe, so on
    any error it returns a fully redacted placeholder (fail-closed for PII).
    """

    def __init__(self, language: str = "es") -> None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_anonymizer import AnonymizerEngine

        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "es", "model_name": "es_core_news_sm"}],
        })
        self._analyzer = AnalyzerEngine(
            nlp_engine=provider.create_engine(), supported_languages=["es"]
        )
        self._anonymizer = AnonymizerEngine()
        self._language = language

    def scrub(self, text: str) -> str:
        if not text:
            return text
        try:
            results = self._analyzer.analyze(
                text=text, language=self._language, entities=_SCRUB_ENTITIES,
                score_threshold=0.5,
            )
            if not results:
                return text
            return self._anonymizer.anonymize(text=text, analyzer_results=results).text
        except Exception:
            # Fail-closed: if we cannot verify the text is clean, redact it all
            # rather than risk leaking PII to the observability backend.
            logger.warning("Fallo al anonimizar texto para trazas; se redacta por completo")
            return "[REDACTED]"
