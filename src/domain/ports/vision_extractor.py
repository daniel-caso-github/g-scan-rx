from abc import ABC, abstractmethod

from src.domain.entities.medicamento_extraido import MedicamentoExtraido


class VisionExtractor(ABC):
    """Port: extrae medicamentos de una imagen de receta usando un VLM."""

    @abstractmethod
    async def extract(self, image_bytes: bytes) -> list[MedicamentoExtraido]:
        """Segmenta la receta y extrae líneas de medicamentos con confianza por campo."""
        ...
