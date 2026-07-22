from abc import ABC, abstractmethod

from src.domain.entities.extracted_medication import ExtractedMedication


class VisionExtractor(ABC):
    """Port: extracts medications from a prescription image using a VLM."""

    @abstractmethod
    async def extract(self, image_bytes: bytes) -> list[ExtractedMedication]:
        """Segments the prescription and extracts medication lines with per-field confidence."""
        ...
