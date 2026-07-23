from __future__ import annotations

import asyncio
import math
from typing import Any

from src.domain.entities.catalog_item import CatalogItem
from src.domain.ports.retriever import Retriever
from src.infrastructure.embedding.embedder import Embedder


class HybridRetriever(Retriever):
    def __init__(
        self,
        corpus: list[CatalogItem],
        embedder: Embedder,
        reranker_model: str = "BAAI/bge-reranker-v2-m3",
        rerank_top_n: int = 20,
    ) -> None:
        self._corpus = corpus
        self._embedder = embedder
        self._reranker_model = reranker_model
        self._rerank_top_n = rerank_top_n
        self._bm25: Any | None = None
        self._corpus_texts: list[str] | None = None
        self._corpus_embeddings: list[list[float]] | None = None
        self._reranker: Any | None = None

    async def retrieve(self, query: str, top_k: int = 5) -> list[tuple[CatalogItem, float]]:
        if not self._corpus:
            return []

        if self._bm25 is None:
            self._build_bm25()
        if self._corpus_embeddings is None:
            await asyncio.to_thread(self._build_embeddings)

        bm25_ranking = self._bm25_search(query)
        vector_ranking = await asyncio.to_thread(self._vector_search, query)
        fused = self._rrf_fusion(bm25_ranking, vector_ranking)
        candidates = fused[: self._rerank_top_n]

        try:
            reranked = await asyncio.to_thread(self._rerank, query, candidates)
        except Exception:
            reranked = candidates

        return reranked[:top_k]

    def _build_bm25(self) -> None:
        from rank_bm25 import BM25Okapi

        self._corpus_texts = [Embedder.text_for_item(item) for item in self._corpus]
        tokenized = [text.lower().split() for text in self._corpus_texts]
        self._bm25 = BM25Okapi(tokenized)

    def _build_embeddings(self) -> None:
        if self._corpus_texts is None:
            self._corpus_texts = [Embedder.text_for_item(item) for item in self._corpus]
        self._corpus_embeddings = self._embedder.embed(self._corpus_texts)

    def _bm25_search(self, query: str) -> list[tuple[CatalogItem, float]]:
        scores = self._bm25.get_scores(query.lower().split())
        ranked = sorted(zip(self._corpus, scores, strict=True), key=lambda x: x[1], reverse=True)
        return [(item, float(score)) for item, score in ranked]

    def _vector_search(self, query: str) -> list[tuple[CatalogItem, float]]:
        query_emb = self._embedder.embed_one(query)
        similarities = [
            self._cosine_similarity(query_emb, emb) for emb in self._corpus_embeddings
        ]
        ranked = sorted(
            zip(self._corpus, similarities, strict=True), key=lambda x: x[1], reverse=True
        )
        return [(item, float(s)) for item, s in ranked]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _rrf_score(rank: int, k: int = 60) -> float:
        return 1.0 / (k + rank + 1)

    def _rrf_fusion(
        self,
        bm25_ranking: list[tuple[CatalogItem, float]],
        vector_ranking: list[tuple[CatalogItem, float]],
    ) -> list[tuple[CatalogItem, float]]:
        scores: dict[str, float] = {}
        items_by_id: dict[str, CatalogItem] = {}

        for rank, (item, _) in enumerate(bm25_ranking):
            scores[item.id] = scores.get(item.id, 0.0) + self._rrf_score(rank)
            items_by_id[item.id] = item

        for rank, (item, _) in enumerate(vector_ranking):
            scores[item.id] = scores.get(item.id, 0.0) + self._rrf_score(rank)
            items_by_id[item.id] = item

        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(items_by_id[item_id], score) for item_id, score in sorted_ids]

    def _rerank(
        self, query: str, candidates: list[tuple[CatalogItem, float]]
    ) -> list[tuple[CatalogItem, float]]:
        if not candidates:
            return candidates
        try:
            from sentence_transformers import CrossEncoder

            if self._reranker is None:
                self._reranker = CrossEncoder(self._reranker_model)
            pairs = [(query, Embedder.text_for_item(item)) for item, _ in candidates]
            reranker_scores = self._reranker.predict(pairs)
            reranked = sorted(
                zip([item for item, _ in candidates], reranker_scores, strict=True),
                key=lambda x: x[1],
                reverse=True,
            )
            return [(item, float(s)) for item, s in reranked]
        except Exception:
            return candidates
