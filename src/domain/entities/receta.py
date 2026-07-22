from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from src.domain.entities.medicamento_extraido import MedicamentoExtraido


class EstadoReceta(StrEnum):
    pendiente = "pendiente"
    verificada = "verificada"
    confirmada = "confirmada"


class Receta(BaseModel):
    """Imagen de receta médica manuscrita que entra al sistema.

    NUNCA contiene datos reales de pacientes; solo image_hash como
    huella de la imagen (regla cero-datos-reales).
    """

    id: str
    image_hash: str
    medicamentos: list[MedicamentoExtraido] = []
    processed_at: datetime | None = None
    status: EstadoReceta = EstadoReceta.pendiente

    model_config = {"frozen": True}
