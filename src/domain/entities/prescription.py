from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from src.domain.entities.extracted_medication import ExtractedMedication


class PrescriptionStatus(StrEnum):
    pending = "pending"
    verified = "verified"
    confirmed = "confirmed"


class Prescription(BaseModel):
    """Handwritten medical prescription image entering the system.

    NEVER contains real patient data; only image_hash as the image
    fingerprint (cero-datos-reales rule).
    """

    id: str
    image_hash: str
    medications: list[ExtractedMedication] = []
    processed_at: datetime | None = None
    status: PrescriptionStatus = PrescriptionStatus.pending

    model_config = {"frozen": True}
