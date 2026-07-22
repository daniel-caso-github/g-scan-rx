from __future__ import annotations

import hashlib
import math

import pytest

from src.domain.entities.catalog_item import CatalogItem
from src.infrastructure.embedding.embedder import Embedder
from src.infrastructure.retrieval.hybrid_retriever import HybridRetriever


class FakeEmbedder(Embedder):
    """Deterministic embedder with no real models."""

    DIM = 16

    def __init__(self) -> None:
        self._model_name = "fake"
        self._model = "fake"

    def _get_model(self):
        return self

    def embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            h = int(hashlib.md5(text.encode()).hexdigest(), 16)
            vec = [(h >> i & 0xFF) / 255.0 for i in range(self.DIM)]
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            results.append([x / norm for x in vec])
        return results

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


@pytest.fixture(scope="module")
def catalog():
    from src.data.synthetic.catalog_seed import get_seed_catalog

    return get_seed_catalog()


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()


@pytest.fixture
def retriever(catalog, fake_embedder):
    return HybridRetriever(corpus=catalog, embedder=fake_embedder)


@pytest.mark.asyncio
async def test_retrieve_returns_top_k(retriever):
    results = await retriever.retrieve("amoxicilina", top_k=3)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_retrieve_returns_list_of_tuples(retriever):
    results = await retriever.retrieve("ibuprofeno", top_k=2)
    for item, score in results:
        assert isinstance(item, CatalogItem)
        assert isinstance(score, float)


@pytest.mark.asyncio
async def test_retrieve_scores_non_negative(retriever):
    results = await retriever.retrieve("paracetamol", top_k=5)
    assert all(score >= 0 for _, score in results)


@pytest.mark.asyncio
async def test_retrieve_descending_order(retriever):
    results = await retriever.retrieve("metformina", top_k=5)
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_retrieve_empty_corpus(fake_embedder):
    r = HybridRetriever(corpus=[], embedder=fake_embedder)
    results = await r.retrieve("amoxicilina", top_k=3)
    assert results == []


def test_rrf_fusion_sums_scores_when_in_both(catalog, fake_embedder):
    retriever = HybridRetriever(corpus=catalog, embedder=fake_embedder)
    retriever._build_bm25()

    bm25_ranking = [(catalog[0], 1.0), (catalog[1], 0.5)]
    vector_ranking = [(catalog[0], 0.9), (catalog[2], 0.8)]

    fused = retriever._rrf_fusion(bm25_ranking, vector_ranking)

    fused_ids = [item.id for item, _ in fused]
    assert fused_ids[0] == catalog[0].id


def test_cosine_similarity_vector_with_itself():
    v = [0.6, 0.8]
    sim = HybridRetriever._cosine_similarity(v, v)
    assert abs(sim - 1.0) < 1e-6


def test_cosine_similarity_orthogonal_vectors():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    sim = HybridRetriever._cosine_similarity(a, b)
    assert abs(sim) < 1e-6


def test_rrf_score_decreases_with_rank():
    r0 = HybridRetriever._rrf_score(0)
    r5 = HybridRetriever._rrf_score(5)
    r10 = HybridRetriever._rrf_score(10)
    assert r0 > r5 > r10
