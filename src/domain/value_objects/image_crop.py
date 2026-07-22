from pydantic import BaseModel, field_validator


class ImageCrop(BaseModel):
    """Region of the original image (bounding box) that originated an extracted field."""

    bbox: tuple[int, int, int, int]  # x, y, w, h in pixels
    crop_ref: str  # path or handle to the rendered crop

    model_config = {"frozen": True}

    @field_validator("bbox")
    @classmethod
    def bbox_positive(cls, v: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x, y, w, h = v
        if w <= 0 or h <= 0:
            raise ValueError("bbox width and height must be positive")
        if x < 0 or y < 0:
            raise ValueError("bbox coordinates cannot be negative")
        return v
