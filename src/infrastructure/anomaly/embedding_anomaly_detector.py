from __future__ import annotations

import logging
import math

from src.domain.ports.anomaly_detector import AnomalyDetector
from src.infrastructure.embedding.embedder import Embedder

logger = logging.getLogger(__name__)

# Reference phrases that describe what an in-distribution prescription looks
# like. The centroid of their embeddings is the "prescription" region; inputs
# far from it are treated as out-of-distribution (not a prescription).
_REFERENCE_TEXTS: tuple[str, ...] = (
    "receta médica manuscrita con medicamentos, dosis y frecuencia",
    "prescripción de fármacos: nombre del medicamento, miligramos, vía oral",
    "indicación médica: tomar comprimidos cada 8 horas durante 7 días",
    "antibiótico 500 mg cada 12 horas por vía oral",
    "analgésico en dosis de 400 mg administrado cada 8 horas",
)


class EmbeddingAnomalyDetector(AnomalyDetector):
    """OOD detector: flags content that does not resemble a prescription.

    Reuses the text ``Embedder``. At construction it embeds a set of reference
    prescription phrases and stores their centroid. An input is scored by cosine
    distance to that centroid; distant inputs get a high anomaly score.

    The port receives ``image_bytes``. This detector can only judge textual
    content (bge-m3 is a text encoder), so it scores the payload when it decodes
    as UTF-8 text (e.g. OCR text or a synthetic caption). Binary image bytes it
    cannot embed yield a low score (defer the decision to downstream extraction),
    honoring the fail-safe contract: never abstain spuriously on unjudgeable input.
    """

    def __init__(
        self,
        embedder: Embedder,
        threshold: float = 0.5,
        reference_texts: tuple[str, ...] = _REFERENCE_TEXTS,
    ) -> None:
        self._embedder = embedder
        self._threshold = threshold
        self._reference_texts = reference_texts
        self._centroid: list[float] | None = None

    def _get_centroid(self) -> list[float]:
        if self._centroid is None:
            embeddings = self._embedder.embed(list(self._reference_texts))
            dims = len(embeddings[0])
            centroid = [
                sum(emb[i] for emb in embeddings) / len(embeddings) for i in range(dims)
            ]
            self._centroid = _l2_normalize(centroid)
        return self._centroid

    async def score(self, image_bytes: bytes) -> float:
        text = self._decode_text(image_bytes)
        if text is None:
            # Cannot judge binary image content with a text encoder: defer.
            return 0.0
        return self.score_text(text)

    def score_text(self, text: str) -> float:
        if not text.strip():
            return 0.0
        try:
            centroid = self._get_centroid()
            embedding = _l2_normalize(self._embedder.embed_one(text))
        except Exception:
            # Fail-safe: never abstain because scoring itself broke.
            logger.warning("Fallo al calcular embedding OOD; se retorna score bajo")
            return 0.0
        similarity = _cosine(embedding, centroid)
        # Map cosine similarity in [-1, 1] to an anomaly score in [0, 1]:
        # high similarity -> low anomaly; low/negative similarity -> high anomaly.
        return max(0.0, min(1.0, (1.0 - similarity) / 2.0))

    def is_anomaly(self, score: float) -> bool:
        return score > self._threshold

    @staticmethod
    def _decode_text(image_bytes: bytes) -> str | None:
        try:
            text = image_bytes.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            return None
        # Reject strings that carry non-printable/binary noise (likely an image).
        if any(ord(ch) < 9 for ch in text):
            return None
        return text


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))
