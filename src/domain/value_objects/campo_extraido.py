from enum import StrEnum

from pydantic import BaseModel, field_validator

from src.domain.value_objects.recorte_imagen import RecorteImagen


class EstadoCampo(StrEnum):
    legible = "legible"
    dudoso = "dudoso"
    ilegible = "ilegible"


class CampoExtraido(BaseModel):
    """Unidad atómica de extracción: campo + confianza + estado de legibilidad.

    Si confidence < umbral_calibrado → status=ilegible, value=None.
    Nunca se inventa un valor (regla abstencion-obligatoria).
    """

    value: str | None
    confidence: float  # [0.0, 1.0]
    status: EstadoCampo
    source_crop: RecorteImagen

    model_config = {"frozen": True}

    @field_validator("confidence")
    @classmethod
    def confidence_rango(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence debe estar en [0.0, 1.0]")
        return v

    @field_validator("value")
    @classmethod
    def value_consistente_con_status(cls, v: str | None) -> str | None:
        return v

    def model_post_init(self, __context: object) -> None:
        if self.status == EstadoCampo.ilegible and self.value is not None:
            raise ValueError("campo ilegible no puede tener value; debe ser None")
        if self.status == EstadoCampo.legible and self.value is None:
            raise ValueError("campo legible debe tener value")
