from pydantic import BaseModel

from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop


class ExtractedMedication(BaseModel):
    """One medication line as read by the VLM, before verification.

    Each field carries its own confidence; abstention operates per field,
    not per entire line.
    """

    drug: ExtractedField
    dose: ExtractedField
    frequency: ExtractedField
    duration: ExtractedField
    route: ExtractedField
    crop: ImageCrop  # region covering the full medication line

    model_config = {"frozen": True}

    @property
    def has_unreadable_field(self) -> bool:
        fields = [self.drug, self.dose, self.frequency, self.duration, self.route]
        return any(f.status == FieldStatus.unreadable for f in fields)

    @property
    def min_confidence(self) -> float:
        fields = [self.drug, self.dose, self.frequency, self.duration, self.route]
        return min(f.confidence for f in fields)
