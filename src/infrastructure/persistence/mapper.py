from src.domain.entities.catalog_item import CatalogItem
from src.infrastructure.persistence.orm_models import CatalogItemORM


def orm_to_domain(orm: CatalogItemORM) -> CatalogItem:
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


def domain_to_orm_values(item: CatalogItem) -> dict:
    return {
        "id": item.id,
        "active_ingredient": item.active_ingredient,
        "brand_name": item.brand_name,
        "presentation": item.presentation,
        "concentration": item.concentration,
        "form": item.form,
        "dose_range": item.dose_range,
        "source": item.source,
        "country": item.country,
        "embedding": item.embedding,
    }
