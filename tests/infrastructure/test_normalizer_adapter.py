import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.infrastructure.normalizer.mlx_normalizer_adapter import MlxNormalizerAdapter


def _make_crop() -> ImageCrop:
    return ImageCrop(bbox=(0, 0, 10, 10), crop_ref="test")


def _make_client_returning(payload: dict) -> MagicMock:
    content = json.dumps(payload)
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


async def test_normalize_readable_field():
    client = _make_client_returning({"amount": 500.0, "unit": "mg", "route": "oral"})
    adapter = MlxNormalizerAdapter(client=client, model="gscan-norm-v1")
    field = ExtractedField(
        value="500mg",
        confidence=0.9,
        status=FieldStatus.readable,
        source_crop=_make_crop(),
    )

    result = await adapter.normalize_dose(field)

    assert isinstance(result, NormalizedDose)
    assert result.amount == 500.0
    assert result.unit == "mg"
    assert result.route == "oral"
    client.chat.completions.create.assert_awaited_once()


async def test_normalize_unreadable_returns_none():
    client = MagicMock()
    client.chat.completions.create = AsyncMock()
    adapter = MlxNormalizerAdapter(client=client, model="gscan-norm-v1")
    field = ExtractedField(
        value=None,
        confidence=0.1,
        status=FieldStatus.unreadable,
        source_crop=_make_crop(),
    )

    result = await adapter.normalize_dose(field)

    assert result is None
    client.chat.completions.create.assert_not_awaited()


async def test_normalize_returns_none_on_api_error():
    client = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("conexión rechazada"))
    adapter = MlxNormalizerAdapter(client=client, model="gscan-norm-v1")
    field = ExtractedField(
        value="500mg",
        confidence=0.9,
        status=FieldStatus.readable,
        source_crop=_make_crop(),
    )

    result = await adapter.normalize_dose(field)

    assert result is None


async def test_normalize_returns_none_on_invalid_unit():
    client = _make_client_returning({"amount": 5.0, "unit": "tabletas", "route": "oral"})
    adapter = MlxNormalizerAdapter(client=client, model="gscan-norm-v1")
    field = ExtractedField(
        value="5 tabletas",
        confidence=0.85,
        status=FieldStatus.readable,
        source_crop=_make_crop(),
    )

    result = await adapter.normalize_dose(field)

    assert result is None


async def test_normalize_uncertain_field():
    client = _make_client_returning({"amount": 250.0, "unit": "mg", "route": "oral"})
    adapter = MlxNormalizerAdapter(client=client, model="gscan-norm-v1")
    field = ExtractedField(
        value="250mg aprox",
        confidence=0.5,
        status=FieldStatus.uncertain,
        source_crop=_make_crop(),
    )

    result = await adapter.normalize_dose(field)

    assert isinstance(result, NormalizedDose)
    assert result.amount == 250.0
    client.chat.completions.create.assert_awaited_once()
