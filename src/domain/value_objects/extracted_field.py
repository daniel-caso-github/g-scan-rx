from enum import StrEnum

from pydantic import BaseModel, field_validator

from src.domain.value_objects.image_crop import ImageCrop


class FieldStatus(StrEnum):
    readable = "readable"
    uncertain = "uncertain"
    unreadable = "unreadable"


class ExtractedField(BaseModel):
    """Atomic extraction unit: field value + confidence + readability status.

    If confidence < calibrated_threshold → status=unreadable, value=None.
    Values are never invented (abstencion-obligatoria rule).
    """

    value: str | None
    confidence: float  # [0.0, 1.0]
    status: FieldStatus
    source_crop: ImageCrop

    model_config = {"frozen": True}

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be in [0.0, 1.0]")
        return v

    @field_validator("value")
    @classmethod
    def value_consistent_with_status(cls, v: str | None) -> str | None:
        return v

    def model_post_init(self, __context: object) -> None:
        if self.status == FieldStatus.unreadable and self.value is not None:
            raise ValueError("unreadable field cannot have a value; must be None")
        if self.status == FieldStatus.readable and self.value is None:
            raise ValueError("readable field must have a value")
