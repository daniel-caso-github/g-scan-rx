from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.ingest_catalog import IngestCatalogUseCase
from src.data.synthetic.catalog_seed import get_seed_catalog


@pytest.fixture
def catalog():
    return get_seed_catalog()


@pytest.fixture
def mock_source(catalog):
    source = MagicMock()
    source.fetch_all = AsyncMock(return_value=catalog[:3])
    return source


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def use_case(mock_source, mock_repository):
    return IngestCatalogUseCase(source=mock_source, repository=mock_repository)


async def test_execute_upserts_all_items(use_case, mock_repository):
    await use_case.execute()
    assert mock_repository.upsert.call_count == 3


async def test_execute_captures_error_without_breaking(mock_source, mock_repository, catalog):
    mock_source.fetch_all = AsyncMock(return_value=catalog[:3])
    mock_repository.upsert.side_effect = [None, Exception("DB error"), None]
    uc = IngestCatalogUseCase(source=mock_source, repository=mock_repository)
    result = await uc.execute()
    assert mock_repository.upsert.call_count == 3
    assert len(result.errors) == 1


async def test_execute_returns_correct_totals(use_case):
    result = await use_case.execute()
    assert result.total_fetched == 3
    assert result.total_upserted == 3
