from src.domain.entities.prescription import Prescription
from src.domain.ports.image_cache import ImageCache


class NullImageCache(ImageCache):
    """No-op cache. Every lookup is a miss; sets are discarded."""

    async def get(self, image_hash: str) -> Prescription | None:
        return None

    async def set(self, image_hash: str, prescription: Prescription) -> None:
        pass
