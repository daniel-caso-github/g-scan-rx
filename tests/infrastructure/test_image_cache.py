import pytest

from src.data.synthetic.catalog_seed import get_seed_catalog
from src.data.synthetic.generator import PrescriptionGenerator
from src.infrastructure.cache.memory_image_cache import MemoryImageCache
from src.infrastructure.cache.null_image_cache import NullImageCache


def _make_prescription():
    catalog = get_seed_catalog()
    gen = PrescriptionGenerator(catalog=catalog, seed=0)
    return gen.generate(n=1)[0]


@pytest.mark.asyncio
async def test_null_cache_always_misses():
    cache = NullImageCache()
    assert await cache.get("abc") is None


@pytest.mark.asyncio
async def test_null_cache_set_is_noop():
    cache = NullImageCache()
    p = _make_prescription()
    await cache.set("abc", p)
    assert await cache.get("abc") is None


@pytest.mark.asyncio
async def test_memory_cache_hit_after_set():
    cache = MemoryImageCache(maxsize=10)
    p = _make_prescription()
    await cache.set("hash1", p)
    result = await cache.get("hash1")
    assert result is not None
    assert result.id == p.id


@pytest.mark.asyncio
async def test_memory_cache_miss_for_unknown_hash():
    cache = MemoryImageCache(maxsize=10)
    assert await cache.get("nonexistent") is None


@pytest.mark.asyncio
async def test_memory_cache_evicts_lru_when_full():
    cache = MemoryImageCache(maxsize=2)
    p1 = _make_prescription()
    p2 = _make_prescription()
    p3 = _make_prescription()
    await cache.set("h1", p1)
    await cache.set("h2", p2)
    await cache.set("h3", p3)
    assert await cache.get("h1") is None
    assert await cache.get("h3") is not None
