from abc import ABC, abstractmethod

from src.domain.entities.prescription import Prescription


class ImageCache(ABC):
    """Port: caches extraction results keyed by image hash to avoid redundant VLM calls."""

    @abstractmethod
    async def get(self, image_hash: str) -> Prescription | None: ...

    @abstractmethod
    async def set(self, image_hash: str, prescription: Prescription) -> None: ...
