from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector as PgVector
from sqlalchemy import JSON, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CatalogItemORM(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (
        Index(
            "ix_catalog_items_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    active_ingredient: Mapped[str] = mapped_column(String, nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String, nullable=True)
    presentation: Mapped[str] = mapped_column(String, nullable=False)
    concentration: Mapped[str | None] = mapped_column(String, nullable=True)
    form: Mapped[str | None] = mapped_column(String, nullable=True)
    dose_range: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding: Mapped[Any] = mapped_column(PgVector(768), nullable=True)
