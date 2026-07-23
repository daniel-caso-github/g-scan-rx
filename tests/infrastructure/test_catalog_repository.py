from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.catalog_item import CatalogItem
from src.domain.services.make_id import make_id

_SA_PATCH = {
    "sqlalchemy": MagicMock(),
    "sqlalchemy.dialects": MagicMock(),
    "sqlalchemy.dialects.postgresql": MagicMock(),
    "sqlalchemy.ext": MagicMock(),
    "sqlalchemy.ext.asyncio": MagicMock(),
    "src.infrastructure.persistence.orm_models": MagicMock(),
}


@pytest.fixture
def item():
    return CatalogItem(
        id=make_id("cima", "amoxicilina", "cápsula 500 mg"),
        active_ingredient="amoxicilina",
        brand_name="Amoxil",
        presentation="cápsula 500 mg",
        source="cima",
    )


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    with patch.dict("sys.modules", _SA_PATCH):
        from src.infrastructure.persistence.catalog_repository import SqlAlchemyCatalogRepository
        return SqlAlchemyCatalogRepository(session=mock_session)


@pytest.mark.asyncio
async def test_upsert_executes_and_commits(repository, mock_session, item):
    with patch.dict("sys.modules", _SA_PATCH):
        await repository.upsert(item)
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_no_result(mock_session, item):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=result_mock)

    with patch.dict("sys.modules", _SA_PATCH):
        from src.infrastructure.persistence.catalog_repository import SqlAlchemyCatalogRepository
        repo = SqlAlchemyCatalogRepository(session=mock_session)
        result = await repo.get_by_id(item.id)

    assert result is None


@pytest.mark.asyncio
async def test_count_returns_integer(mock_session):
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = 5
    mock_session.execute = AsyncMock(return_value=result_mock)

    with patch.dict("sys.modules", _SA_PATCH):
        from src.infrastructure.persistence.catalog_repository import SqlAlchemyCatalogRepository
        repo = SqlAlchemyCatalogRepository(session=mock_session)
        total = await repo.count()

    assert total == 5
