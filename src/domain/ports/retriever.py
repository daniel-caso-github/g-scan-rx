from abc import ABC, abstractmethod

from src.domain.entities.catalog_item import CatalogItem


class Retriever(ABC):
    """Port: hybrid catalog retrieval (BM25 + vector + reranker)."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> list[tuple[CatalogItem, float]]:
        """Returns a list of (item, score) sorted by descending relevance."""
        ...
