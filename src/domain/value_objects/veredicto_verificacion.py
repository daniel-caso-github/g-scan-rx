from enum import StrEnum

from pydantic import BaseModel, field_validator


class EstadoVeredicto(StrEnum):
    verificado = "verificado"
    dudoso = "dudoso"
    no_encontrado = "no_encontrado"


class VeredictoVerificacion(BaseModel):
    """Resultado de contrastar un campo contra el catálogo oficial.

    Contrato de fallo: ante error del verificador tras reintento →
    status=dudoso con nota "verificación no disponible". Nunca levanta
    excepción hacia el pipeline.
    """

    status: EstadoVeredicto
    catalog_item_id: str | None = None
    match_score: float = 0.0
    notes: list[str] = []

    model_config = {"frozen": True}

    @field_validator("match_score")
    @classmethod
    def score_rango(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("match_score debe estar en [0.0, 1.0]")
        return v

    def model_post_init(self, __context: object) -> None:
        if self.status == EstadoVeredicto.verificado and self.catalog_item_id is None:
            raise ValueError("veredicto 'verificado' requiere catalog_item_id")

    @classmethod
    def no_disponible(cls) -> "VeredictoVerificacion":
        return cls(
            status=EstadoVeredicto.dudoso,
            notes=["verificación no disponible"],
        )
