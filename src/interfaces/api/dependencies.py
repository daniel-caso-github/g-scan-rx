from functools import lru_cache

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.infrastructure.config import settings
from src.infrastructure.normalizer.mlx_normalizer_adapter import MlxNormalizerAdapter
from src.infrastructure.vision.claude_vision_adapter import ClaudeVisionAdapter


@lru_cache
def get_extract_prescription_use_case() -> ExtractPrescriptionUseCase:
    extractor = ClaudeVisionAdapter(
        client=AsyncAnthropic(api_key=settings.anthropic_api_key),
        model=settings.vision_model,
        readable_threshold=settings.vision_confidence_readable,
        uncertain_threshold=settings.vision_confidence_uncertain,
    )
    normalizer = MlxNormalizerAdapter(
        client=AsyncOpenAI(base_url=settings.normalizer_url, api_key="local"),
        model=settings.normalizer_model,
    )
    return ExtractPrescriptionUseCase(extractor=extractor, normalizer=normalizer)
