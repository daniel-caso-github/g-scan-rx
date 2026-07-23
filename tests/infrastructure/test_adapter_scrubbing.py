import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

from src.domain.ports.text_scrubber import TextScrubber
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.infrastructure.normalizer.gemini_normalizer_adapter import GeminiNormalizerAdapter
from src.infrastructure.vision.gemini_vision_adapter import GeminiVisionAdapter


class _RecordingScrubber(TextScrubber):
    def __init__(self):
        self.seen = []

    def scrub(self, text: str) -> str:
        self.seen.append(text)
        return "[SCRUBBED]"


class _RecordingObs:
    def __init__(self):
        self.updates = []

    def update(self, **kwargs):
        self.updates.append(kwargs)


class _RecordingTracer:
    def __init__(self):
        self.obs = _RecordingObs()

    def span(self, name, **kwargs):
        from contextlib import nullcontext
        return nullcontext()

    @contextmanager
    def generation(self, name, model, input):
        self.captured_input = input
        yield self.obs

    def flush(self):
        pass


def _vision_client(text):
    response = MagicMock()
    response.text = text
    response.usage_metadata = None
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_vision_adapter_scrubs_output_before_tracing():
    payload = json.dumps({"medications": []})
    tracer = _RecordingTracer()
    scrubber = _RecordingScrubber()
    adapter = GeminiVisionAdapter(
        client=_vision_client(payload), model="m",
        readable_threshold=0.7, uncertain_threshold=0.3,
        tracer=tracer, scrubber=scrubber,
    )
    await adapter.extract(b"fake")

    assert scrubber.seen  # scrubber was called on the raw output
    assert tracer.obs.updates[0]["output"] == "[SCRUBBED]"


def _norm_client(text):
    response = MagicMock()
    response.text = text
    response.usage_metadata = None
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


async def test_normalizer_adapter_scrubs_input_and_output():
    tracer = _RecordingTracer()
    scrubber = _RecordingScrubber()
    adapter = GeminiNormalizerAdapter(
        client=_norm_client(json.dumps({"amount": 500.0, "unit": "mg", "route": "oral"})),
        model="m", tracer=tracer, scrubber=scrubber,
    )
    field = ExtractedField(
        value="500 mg Juan", confidence=0.9, status=FieldStatus.readable,
        source_crop=ImageCrop(bbox=(0, 0, 1, 1), crop_ref="x"),
    )
    await adapter.normalize_dose(field)

    # Traced input was scrubbed, not the raw value.
    assert tracer.captured_input["value"] == "[SCRUBBED]"
    # Traced output was scrubbed too.
    assert tracer.obs.updates[0]["output"] == "[SCRUBBED]"
