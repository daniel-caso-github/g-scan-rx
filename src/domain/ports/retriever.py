from abc import ABC, abstractmethod

from src.domain.entities.item_catalogo import ItemCatalogo


class Retriever(ABC):
    """Port: recuperación híbrida de ítems del catálogo (BM25 + vectorial + reranker)."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> list[tuple[ItemCatalogo, float]]:
        """Devuelve lista de (ítem, score) ordenada por relevancia descendente."""
        ...
