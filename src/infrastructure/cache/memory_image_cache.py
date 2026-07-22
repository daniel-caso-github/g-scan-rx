import asyncio
import logging

from cachetools import LRUCache

from src.domain.entities.prescription import Prescription
from src.domain.ports.image_cache import ImageCache

logger = logging.getLogger(__name__)


class MemoryImageCache(ImageCache):
    """In-process LRU cache of extraction results keyed by image SHA-256 hash.

    Thread-safe via asyncio.Lock. Evicts least-recently-used entries when maxsize is reached.
    """

    def __init__(self, maxsize: int = 256) -> None:
        self._cache: LRUCache = LRUCache(maxsize=maxsize)
        self._lock = asyncio.Lock()

    async def get(self, image_hash: str) -> Prescription | None:
        async with self._lock:
            return self._cache.get(image_hash)

    async def set(self, image_hash: str, prescription: Prescription) -> None:
        async with self._lock:
            self._cache[image_hash] = prescription
        logger.debug("cache: almacenado image_hash=%s (size=%d)", image_hash, len(self._cache))
