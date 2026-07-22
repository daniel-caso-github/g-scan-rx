from __future__ import annotations
from typing import Any

from src.domain.entities.catalog_item import CatalogItem
from src.domain.ports.catalog_repository import CatalogRepository


class SqlAlchemyCatalogRepository(CatalogRepository):
    def __init__(self, session: Any) -> None:
        self._session = session

    async def upsert(self, item: CatalogItem) -> None:
        from sqlalchemy.dialects.postgresql import insert
        from src.infrastructure.persistence.orm_models import CatalogItemORM

        stmt = insert(CatalogItemORM).values(
            id=item.id,
            active_ingredient=item.active_ingredient,
            brand_name=item.brand_name,
            presentation=item.presentation,
            concentration=item.concentration,
            form=item.form,
            dose_range=item.dose_range,
            source=item.source,
            country=item.country,
            embedding=item.embedding,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_=dict(
                active_ingredient=item.active_ingredient,
                brand_name=item.brand_name,
                presentation=item.presentation,
                concentration=item.concentration,
                form=item.form,
                dose_range=item.dose_range,
                source=item.source,
                country=item.country,
                embedding=item.embedding,
            ),
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_by_id(self, item_id: str) -> CatalogItem | None:
        from sqlalchemy import select
        from src.infrastructure.persistence.orm_models import CatalogItemORM

        stmt = select(CatalogItemORM).where(CatalogItemORM.id == item_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return self._to_domain(orm)

    async def count(self) -> int:
        from sqlalchemy import func, select
        from src.infrastructure.persistence.orm_models import CatalogItemORM

        stmt = select(func.count()).select_from(CatalogItemORM)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _to_domain(self, orm: Any) -> CatalogItem:
        return CatalogItem(
            id=orm.id,
            active_ingredient=orm.active_ingredient,
            brand_name=orm.brand_name,
            presentation=orm.presentation,
            concentration=orm.concentration,
            form=orm.form,
            dose_range=orm.dose_range,
            source=orm.source,
            country=orm.country,
            embedding=list(orm.embedding) if orm.embedding is not None else None,
        )
