import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.value_objects.extracted_field import FieldStatus
from src.infrastructure.vision.gemini_vision_adapter import GeminiVisionAdapter

READABLE_THRESHOLD = 0.7
UNCERTAIN_THRESHOLD = 0.3


def _make_adapter(mock_client) -> GeminiVisionAdapter:
    return GeminiVisionAdapter(
        client=mock_client,
        model="gemini-2.0-flash",
        readable_threshold=READABLE_THRESHOLD,
        uncertain_threshold=UNCERTAIN_THRESHOLD,
    )


def _make_client(response_text: str):
    response = MagicMock()
    response.text = response_text

    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


def _single_med_payload(
    drug_value="Amoxicilina",
    drug_conf=0.95,
    dose_value="500mg",
    dose_conf=0.88,
    freq_value="cada 8h",
    freq_conf=0.72,
    dur_value=None,
    dur_conf=0.10,
    route_value="oral",
    route_conf=0.91,
) -> str:
    return json.dumps({
        "medications": [{
            "drug": {"value": drug_value, "confidence": drug_conf, "bbox": [10, 20, 150, 40]},
            "dose": {"value": dose_value, "confidence": dose_conf, "bbox": [160, 20, 230, 40]},
            "frequency": {"value": freq_value, "confidence": freq_conf, "bbox": [240, 20, 320, 40]},
            "duration": {"value": dur_value, "confidence": dur_conf, "bbox": None},
            "route": {"value": route_value, "confidence": route_conf, "bbox": [330, 20, 390, 40]},
        }]
    })


async def test_extract_readable_field():
    client = _make_client(_single_med_payload(drug_conf=0.95))
    adapter = _make_adapter(client)
    results = await adapter.extract(b"fake-image")
    assert len(results) == 1
    assert results[0].drug.status == FieldStatus.readable
    assert results[0].drug.value == "Amoxicilina"


async def test_extract_uncertain_field():
    client = _make_client(_single_med_payload(freq_conf=0.50))
    adapter = _make_adapter(client)
    results = await adapter.extract(b"fake-image")
    assert results[0].frequency.status == FieldStatus.uncertain
    assert results[0].frequency.value == "cada 8h"


async def test_extract_unreadable_field():
    client = _make_client(_single_med_payload(dur_value=None, dur_conf=0.10))
    adapter = _make_adapter(client)
    results = await adapter.extract(b"fake-image")
    assert results[0].duration.status == FieldStatus.unreadable
    assert results[0].duration.value is None


async def test_extract_returns_empty_on_api_error():
    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("api error"))
    adapter = _make_adapter(client)
    results = await adapter.extract(b"fake-image")
    assert results == []


async def test_extract_multiple_medications():
    payload = json.dumps({
        "medications": [
            {
                "drug": {"value": "Amoxicilina", "confidence": 0.95, "bbox": [10, 20, 150, 40]},
                "dose": {"value": "500mg", "confidence": 0.88, "bbox": None},
                "frequency": {"value": "cada 8h", "confidence": 0.80, "bbox": None},
                "duration": {"value": "7 días", "confidence": 0.75, "bbox": None},
                "route": {"value": "oral", "confidence": 0.91, "bbox": None},
            },
            {
                "drug": {"value": "Ibuprofeno", "confidence": 0.90, "bbox": [10, 60, 150, 80]},
                "dose": {"value": "400mg", "confidence": 0.85, "bbox": None},
                "frequency": {"value": "cada 12h", "confidence": 0.78, "bbox": None},
                "duration": {"value": None, "confidence": 0.05, "bbox": None},
                "route": {"value": "oral", "confidence": 0.88, "bbox": None},
            },
        ]
    })
    client = _make_client(payload)
    adapter = _make_adapter(client)
    results = await adapter.extract(b"fake-image")
    assert len(results) == 2
    assert results[0].drug.value == "Amoxicilina"
    assert results[1].drug.value == "Ibuprofeno"


async def test_extract_handles_json_in_codeblock():
    inner = _single_med_payload()
    wrapped = f"```json\n{inner}\n```"
    client = _make_client(wrapped)
    adapter = _make_adapter(client)
    results = await adapter.extract(b"fake-image")
    assert len(results) == 1
    assert results[0].drug.value == "Amoxicilina"
