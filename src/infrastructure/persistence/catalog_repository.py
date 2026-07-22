from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.catalog_item import CatalogItem
from src.domain.ports.catalog_repository import CatalogRepository
from src.infrastructure.persistence.mapper import domain_to_orm_values, orm_to_domain
from src.infrastructure.persistence.orm_models import CatalogItemORM


class SqlAlchemyCatalogRepository(CatalogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, item: CatalogItem) -> None:
        values = domain_to_orm_values(item)
        stmt = (
            insert(CatalogItemORM)
            .values(**values)
            .on_conflict_do_update(index_elements=["id"], set_=values)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_by_id(self, item_id: str) -> CatalogItem | None:
        stmt = select(CatalogItemORM).where(CatalogItemORM.id == item_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return orm_to_domain(orm) if orm is not None else None

    async def count(self) -> int:
        stmt = select(func.count()).select_from(CatalogItemORM)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_all(self) -> list[CatalogItem]:
        stmt = select(CatalogItemORM)
        result = await self._session.execute(stmt)
        return [orm_to_domain(row) for row in result.scalars().all()]
