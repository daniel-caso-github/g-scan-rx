from abc import ABC, abstractmethod

from src.domain.entities.item_catalogo import ItemCatalogo


class CatalogRepository(ABC):
    """Port: persistencia y consulta del catálogo oficial de medicamentos."""

    @abstractmethod
    async def upsert(self, item: ItemCatalogo) -> None:
        """Inserta o actualiza un ítem del catálogo (idempotente por id)."""
        ...

    @abstractmethod
    async def get_by_id(self, item_id: str) -> ItemCatalogo | None:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...
