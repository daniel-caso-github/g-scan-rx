import logging

from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.ports.normalizer import Normalizer
from src.domain.ports.vision_extractor import VisionExtractor
from src.domain.services.make_id import make_id
from src.domain.value_objects.extracted_field import FieldStatus

logger = logging.getLogger(__name__)


class ExtractPrescriptionUseCase:
    def __init__(self, extractor: VisionExtractor, normalizer: Normalizer) -> None:
        self._extractor = extractor
        self._normalizer = normalizer

    async def execute(self, image_bytes: bytes, image_hash: str) -> Prescription:
        medications = await self._extractor.extract(image_bytes)

        if not medications:
            logger.warning("El extractor no devolvió medicamentos para image_hash=%s", image_hash)

        for med in medications:
            if med.dose.status in (FieldStatus.readable, FieldStatus.uncertain):
                normalized = await self._normalizer.normalize_dose(med.dose)
                if normalized is None:
                    logger.debug(
                        "Normalización de dosis devolvió None para image_hash=%s", image_hash
                    )

        return Prescription(
            id=make_id(image_hash),
            image_hash=image_hash,
            medications=medications,
            status=PrescriptionStatus.pending,
        )
