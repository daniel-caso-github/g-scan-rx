import base64
import json
import logging
import re

from anthropic import APIStatusError, AsyncAnthropic, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.ports.vision_extractor import VisionExtractor
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Analiza esta imagen de receta médica manuscrita. Extrae todos los medicamentos presentes.

Para cada medicamento, devuelve un objeto JSON con estos campos exactos:
- drug: {value: string|null, confidence: float, bbox: [x1,y1,x2,y2]|null}
- dose: {value: string|null, confidence: float, bbox: [x1,y1,x2,y2]|null}
- frequency: {value: string|null, confidence: float, bbox: [x1,y1,x2,y2]|null}
- duration: {value: string|null, confidence: float, bbox: [x1,y1,x2,y2]|null}
- route: {value: string|null, confidence: float, bbox: [x1,y1,x2,y2]|null}

confidence es un número entre 0.0 (ilegible) y 1.0 (perfectamente claro).
Si un campo no aparece en la receta o es ilegible, pon value: null y confidence: 0.0.
Devuelve SOLO el JSON con la estructura: {"medications": [...]}"""

_FIELD_NAMES = ("drug", "dose", "frequency", "duration", "route")
_CODEBLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _parse_json(text: str) -> dict:
    match = _CODEBLOCK_RE.search(text)
    return json.loads(match.group(1) if match else text)


def _bbox_to_xywh(bbox: list[int] | None) -> tuple[int, int, int, int]:
    if bbox and len(bbox) == 4:
        x1, y1, x2, y2 = bbox
        w = max(x2 - x1, 1)
        h = max(y2 - y1, 1)
        return (max(x1, 0), max(y1, 0), w, h)
    return (0, 0, 1, 1)


def _build_field(
    field_name: str,
    raw: dict,
    drug_value: str | None,
    readable_threshold: float,
    uncertain_threshold: float,
) -> ExtractedField:
    value = raw.get("value")
    confidence = float(raw.get("confidence", 0.0))
    bbox_raw = raw.get("bbox")

    if confidence >= readable_threshold and value is not None:
        status = FieldStatus.readable
    elif confidence >= uncertain_threshold and value is not None:
        status = FieldStatus.uncertain
    else:
        status = FieldStatus.unreadable
        value = None

    ref_label = drug_value or "unknown"
    crop = ImageCrop(
        bbox=_bbox_to_xywh(bbox_raw),
        crop_ref=f"{ref_label}_{field_name}",
    )
    return ExtractedField(value=value, confidence=confidence, status=status, source_crop=crop)


class ClaudeVisionAdapter(VisionExtractor):
    def __init__(
        self,
        client: AsyncAnthropic,
        model: str,
        readable_threshold: float,
        uncertain_threshold: float,
    ) -> None:
        self._client = client
        self._model = model
        self._readable_threshold = readable_threshold
        self._uncertain_threshold = uncertain_threshold

    async def extract(self, image_bytes: bytes) -> list[ExtractedMedication]:
        try:
            return await self._extract_with_retry(image_bytes)
        except Exception:
            logger.warning("Error al llamar al VLM; devolviendo lista vacía")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, APIStatusError)),
        reraise=True,
    )
    async def _extract_with_retry(self, image_bytes: bytes) -> list[ExtractedMedication]:
        encoded = base64.b64encode(image_bytes).decode()
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": encoded,
                            },
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )

        raw_text = message.content[0].text
        data = _parse_json(raw_text)
        medications: list[ExtractedMedication] = []

        for med_raw in data.get("medications", []):
            drug_raw = med_raw.get("drug", {})
            drug_value = drug_raw.get("value") if drug_raw.get("confidence", 0.0) >= self._uncertain_threshold else None

            fields = {
                name: _build_field(
                    name,
                    med_raw.get(name, {}),
                    drug_value,
                    self._readable_threshold,
                    self._uncertain_threshold,
                )
                for name in _FIELD_NAMES
            }

            line_bbox = _bbox_to_xywh(med_raw.get("drug", {}).get("bbox"))
            crop = ImageCrop(bbox=line_bbox, crop_ref=f"{drug_value or 'unknown'}_line")

            medications.append(ExtractedMedication(**fields, crop=crop))

        return medications
