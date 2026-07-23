from abc import ABC, abstractmethod

from src.domain.entities.catalog_item import CatalogItem


class CatalogSource(ABC):
    """Port: an official medication catalog source (CIMA, DIGEMID, ...).

    Adapters fetch raw catalog data and map it to domain CatalogItem entities.
    """

    @abstractmethod
    async def fetch_all(self, limit: int | None = None) -> list[CatalogItem]:
        """Fetch catalog items, optionally capping the total at `limit`."""
        ...
