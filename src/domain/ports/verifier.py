from abc import ABC, abstractmethod

from src.domain.entities.catalog_item import CatalogItem
from src.domain.value_objects.extracted_field import ExtractedField
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.domain.value_objects.verification_verdict import VerificationVerdict


class Verifier(ABC):
    """Port: verifies an extracted field against a catalog item.

    Never raises an exception toward the pipeline; degrades to
    VerificationVerdict.no_disponible() on network or timeout errors.
    """

    @abstractmethod
    async def verify(
        self,
        drug: ExtractedField,
        dose: NormalizedDose | None,
        candidate: CatalogItem,
    ) -> VerificationVerdict:
        ...
