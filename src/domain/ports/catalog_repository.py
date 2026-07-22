from abc import ABC, abstractmethod

from src.domain.entities.catalog_item import CatalogItem


class CatalogRepository(ABC):
    """Port: persistence and querying of the official drug catalog."""

    @abstractmethod
    async def upsert(self, item: CatalogItem) -> None:
        """Inserts or updates a catalog item (idempotent by id)."""
        ...

    @abstractmethod
    async def get_by_id(self, item_id: str) -> CatalogItem | None:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...
