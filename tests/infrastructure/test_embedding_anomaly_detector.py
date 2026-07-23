from unittest.mock import MagicMock

import pytest

from src.infrastructure.anomaly.embedding_anomaly_detector import EmbeddingAnomalyDetector


def _make_embedder(reference_vec, input_vec):
    """Embedder whose reference texts all map to `reference_vec` (so the
    centroid equals it) and whose single-text input maps to `input_vec`.
    """
    embedder = MagicMock()
    embedder.embed.side_effect = lambda texts: [list(reference_vec) for _ in texts]
    embedder.embed_one.side_effect = lambda text: list(input_vec)
    return embedder


async def test_score_text_low_for_prescription_like_input():
    # Input identical to the reference centroid -> cosine 1.0 -> score 0.0.
    embedder = _make_embedder([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    detector = EmbeddingAnomalyDetector(embedder=embedder)
    assert detector.score_text("amoxicilina 500 mg cada 8 horas") == pytest.approx(0.0)


async def test_score_text_high_for_ood_input():
    # Orthogonal input -> cosine 0.0 -> score 0.5; opposite -> cosine -1 -> 1.0.
    embedder = _make_embedder([1.0, 0.0, 0.0], [-1.0, 0.0, 0.0])
    detector = EmbeddingAnomalyDetector(embedder=embedder)
    score = detector.score_text("texto totalmente ajeno a una receta")
    assert score == pytest.approx(1.0)
    assert detector.is_anomaly(score) is True


async def test_is_anomaly_uses_threshold():
    embedder = _make_embedder([1.0, 0.0], [0.0, 1.0])  # cosine 0 -> score 0.5
    detector = EmbeddingAnomalyDetector(embedder=embedder, threshold=0.6)
    score = detector.score_text("algo")
    assert score == pytest.approx(0.5)
    assert detector.is_anomaly(score) is False


async def test_score_on_binary_image_bytes_defers():
    embedder = _make_embedder([1.0, 0.0], [1.0, 0.0])
    detector = EmbeddingAnomalyDetector(embedder=embedder)
    # PNG magic header: not decodable as clean UTF-8 text -> defer with score 0.
    score = await detector.score(b"\x89PNG\r\n\x1a\n\x00\x01")
    assert score == 0.0
    embedder.embed_one.assert_not_called()


async def test_score_on_utf8_text_bytes_uses_embedder():
    embedder = _make_embedder([1.0, 0.0, 0.0], [-1.0, 0.0, 0.0])
    detector = EmbeddingAnomalyDetector(embedder=embedder)
    score = await detector.score(b"receta de gatos y perros")
    assert score == pytest.approx(1.0)


async def test_score_text_empty_returns_zero():
    embedder = _make_embedder([1.0, 0.0], [1.0, 0.0])
    detector = EmbeddingAnomalyDetector(embedder=embedder)
    assert detector.score_text("   ") == 0.0


async def test_score_fails_safe_on_embedder_error():
    embedder = MagicMock()
    embedder.embed.side_effect = RuntimeError("model down")
    detector = EmbeddingAnomalyDetector(embedder=embedder)
    # Must not raise and must not spuriously abstain.
    assert detector.score_text("cualquier texto") == 0.0
