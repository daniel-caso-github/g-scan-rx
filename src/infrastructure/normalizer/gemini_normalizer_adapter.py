import json
import logging

from google import genai
from google.genai import types
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.domain.ports.normalizer import Normalizer
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.normalized_dose import NormalizedDose

logger = logging.getLogger(__name__)

NORMALIZATION_PROMPT = """\
Normaliza esta dosis médica al formato canónico.

Dosis a normalizar: {value}

Devuelve SOLO este JSON:
{{"amount": <número como float>, "unit": "<unidad canónica>", "route": "<ruta canónica>"}}

Unidades canónicas válidas: mg, mcg, g, ml, l, ui, meq, comprimido, capsula, ampolla, sobre, supositorio, parche, gota, puff, aplicacion
Rutas canónicas válidas: oral, iv, im, sc, topica, inhalatoria, rectal, sublingual, transdermica, oftalmica, otica, nasal

Si no podés normalizar, devuelve: {{"amount": null, "unit": null, "route": null}}\
"""

_VALID_UNITS = {
    "mg", "mcg", "g", "ml", "l", "ui", "meq",
    "comprimido", "capsula", "ampolla", "sobre",
    "supositorio", "parche", "gota", "puff", "aplicacion",
}


class GeminiNormalizerAdapter(Normalizer):
    def __init__(self, client: genai.Client, model: str) -> None:
        self._client = client
        self._model = model

    async def normalize_dose(self, field: ExtractedField) -> NormalizedDose | None:
        if field.status == FieldStatus.unreadable or field.value is None:
            return None

        try:
            raw = await self._call_model(field.value)
        except Exception:
            logger.warning("Fallo al llamar al normalizador Gemini; se retorna None")
            return None

        try:
            data = json.loads(raw)
            amount = data.get("amount")
            unit = data.get("unit")
            route = data.get("route")
            if amount is None or unit is None or unit not in _VALID_UNITS:
                return None
            return NormalizedDose(amount=float(amount), unit=unit, route=route or None)
        except Exception:
            logger.warning("Respuesta del normalizador no parseable o con vocabulario inválido")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _call_model(self, value: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=[NORMALIZATION_PROMPT.format(value=value)],
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return response.text
