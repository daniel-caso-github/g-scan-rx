from functools import lru_cache

from google import genai

from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.infrastructure.config import settings
from src.infrastructure.normalizer.gemini_normalizer_adapter import GeminiNormalizerAdapter
from src.infrastructure.vision.gemini_vision_adapter import GeminiVisionAdapter


@lru_cache
def get_extract_prescription_use_case() -> ExtractPrescriptionUseCase:
    client = genai.Client(api_key=settings.gemini_api_key)
    extractor = GeminiVisionAdapter(
        client=client,
        model=settings.gemini_model,
        readable_threshold=settings.vision_confidence_readable,
        uncertain_threshold=settings.vision_confidence_uncertain,
    )
    normalizer = GeminiNormalizerAdapter(
        client=client,
        model=settings.gemini_model,
    )
    return ExtractPrescriptionUseCase(extractor=extractor, normalizer=normalizer)
