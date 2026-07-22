from pydantic import BaseModel, field_validator


class RecorteImagen(BaseModel):
    """Región de la imagen original (bounding box) que originó un campo extraído."""

    bbox: tuple[int, int, int, int]  # x, y, w, h en píxeles
    crop_ref: str  # ruta o handle del recorte renderizado

    model_config = {"frozen": True}

    @field_validator("bbox")
    @classmethod
    def bbox_positivo(cls, v: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x, y, w, h = v
        if w <= 0 or h <= 0:
            raise ValueError("ancho y alto del bbox deben ser positivos")
        if x < 0 or y < 0:
            raise ValueError("coordenadas del bbox no pueden ser negativas")
        return v
