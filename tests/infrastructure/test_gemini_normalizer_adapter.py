import json
from unittest.mock import AsyncMock, MagicMock

from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.infrastructure.normalizer.gemini_normalizer_adapter import GeminiNormalizerAdapter


def _make_crop() -> ImageCrop:
    return ImageCrop(bbox=(0, 0, 10, 10), crop_ref="test")


def _make_client(payload: dict) -> MagicMock:
    response = MagicMock()
    response.text = json.dumps(payload)

    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_normalize_readable_field():
    client = _make_client({"amount": 500.0, "unit": "mg", "route": "oral"})
    adapter = GeminiNormalizerAdapter(client=client, model="gemini-2.0-flash")
    field = ExtractedField(
        value="500mg", confidence=0.9, status=FieldStatus.readable, source_crop=_make_crop()
    )
    result = await adapter.normalize_dose(field)
    assert isinstance(result, NormalizedDose)
    assert result.amount == 500.0
    assert result.unit == "mg"
    assert result.route == "oral"
    client.aio.models.generate_content.assert_awaited_once()


async def test_normalize_unreadable_returns_none():
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    adapter = GeminiNormalizerAdapter(client=client, model="gemini-2.0-flash")
    field = ExtractedField(
        value=None, confidence=0.1, status=FieldStatus.unreadable, source_crop=_make_crop()
    )
    result = await adapter.normalize_dose(field)
    assert result is None
    client.aio.models.generate_content.assert_not_awaited()


async def test_normalize_returns_none_on_api_error():
    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("conexión rechazada"))
    adapter = GeminiNormalizerAdapter(client=client, model="gemini-2.0-flash")
    field = ExtractedField(
        value="500mg", confidence=0.9, status=FieldStatus.readable, source_crop=_make_crop()
    )
    result = await adapter.normalize_dose(field)
    assert result is None


async def test_normalize_returns_none_on_invalid_unit():
    client = _make_client({"amount": 5.0, "unit": "tabletas", "route": "oral"})
    adapter = GeminiNormalizerAdapter(client=client, model="gemini-2.0-flash")
    field = ExtractedField(
        value="5 tabletas", confidence=0.85, status=FieldStatus.readable, source_crop=_make_crop()
    )
    result = await adapter.normalize_dose(field)
    assert result is None


async def test_normalize_uncertain_field():
    client = _make_client({"amount": 250.0, "unit": "mg", "route": "oral"})
    adapter = GeminiNormalizerAdapter(client=client, model="gemini-2.0-flash")
    field = ExtractedField(
        value="250mg aprox", confidence=0.5, status=FieldStatus.uncertain, source_crop=_make_crop()
    )
    result = await adapter.normalize_dose(field)
    assert isinstance(result, NormalizedDose)
    assert result.amount == 250.0
    client.aio.models.generate_content.assert_awaited_once()
