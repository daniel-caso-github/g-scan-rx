"""create catalog_items table

Revision ID: 0001
Revises:
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "catalog_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("active_ingredient", sa.String(), nullable=False),
        sa.Column("brand_name", sa.String(), nullable=True),
        sa.Column("presentation", sa.String(), nullable=False),
        sa.Column("concentration", sa.String(), nullable=True),
        sa.Column("form", sa.String(), nullable=True),
        sa.Column("dose_range", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_catalog_items_embedding_hnsw",
        "catalog_items",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_items_embedding_hnsw", table_name="catalog_items")
    op.drop_table("catalog_items")
