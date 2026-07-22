from dataclasses import dataclass, field

from src.domain.ports.catalog_repository import CatalogRepository
from src.infrastructure.catalog.cima import CimaClient


@dataclass
class IngestResult:
    total_fetched: int = 0
    total_upserted: int = 0
    errors: list[str] = field(default_factory=list)


class IngestCatalogUseCase:
    def __init__(self, client: CimaClient, repository: CatalogRepository) -> None:
        self._client = client
        self._repository = repository

    async def execute(self, limit: int | None = None) -> IngestResult:
        result = IngestResult()
        items = await self._client.fetch_all(limit=limit)
        result.total_fetched = len(items)
        for item in items:
            try:
                await self._repository.upsert(item)
                result.total_upserted += 1
            except Exception as exc:
                result.errors.append(f"{item.id}: {exc}")
        return result
