from abc import ABC, abstractmethod

from src.domain.value_objects.extracted_field import ExtractedField
from src.domain.value_objects.normalized_dose import NormalizedDose


class Normalizer(ABC):
    """Port: normalizes raw text extracted by the VLM into canonical structures."""

    @abstractmethod
    async def normalize_dose(self, field: ExtractedField) -> NormalizedDose | None:
        """Converts dose text to canonical units.

        Returns None if normalization cannot be done with sufficient confidence;
        the caller marks the field as uncertain.
        """
        ...
