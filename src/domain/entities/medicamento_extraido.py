from pydantic import BaseModel

from src.domain.value_objects.campo_extraido import CampoExtraido
from src.domain.value_objects.recorte_imagen import RecorteImagen


class MedicamentoExtraido(BaseModel):
    """Una línea de medicamento tal como la leyó el VLM, antes de verificar.

    Cada campo lleva su propia confianza; la abstención opera por campo,
    no por línea completa.
    """

    farmaco: CampoExtraido
    dosis: CampoExtraido
    frecuencia: CampoExtraido
    duracion: CampoExtraido
    via: CampoExtraido
    recorte: RecorteImagen  # región de la línea completa

    model_config = {"frozen": True}

    @property
    def tiene_campo_ilegible(self) -> bool:
        from src.domain.value_objects.campo_extraido import EstadoCampo

        campos = [self.farmaco, self.dosis, self.frecuencia, self.duracion, self.via]
        return any(c.status == EstadoCampo.ilegible for c in campos)

    @property
    def confianza_minima(self) -> float:
        campos = [self.farmaco, self.dosis, self.frecuencia, self.duracion, self.via]
        return min(c.confidence for c in campos)
