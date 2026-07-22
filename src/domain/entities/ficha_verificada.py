from pydantic import BaseModel, model_validator

from src.domain.entities.item_catalogo import ItemCatalogo
from src.domain.value_objects.campo_extraido import CampoExtraido
from src.domain.value_objects.veredicto_verificacion import EstadoVeredicto, VeredictoVerificacion


class CampoVerificado(BaseModel):
    """Campo extraído junto con su veredicto de verificación contra catálogo."""

    campo: CampoExtraido
    veredicto: VeredictoVerificacion

    model_config = {"frozen": True}


class MedicamentoVerificado(BaseModel):
    """Medicamento con todos sus campos verificados contra el catálogo."""

    farmaco: CampoVerificado
    dosis: CampoVerificado
    frecuencia: CampoVerificado
    duracion: CampoVerificado
    via: CampoVerificado
    catalog_match: ItemCatalogo | None = None

    model_config = {"frozen": True}

    @property
    def requiere_revision(self) -> bool:
        from src.domain.value_objects.campo_extraido import EstadoCampo

        campos_verificados = [self.farmaco, self.dosis, self.frecuencia, self.duracion, self.via]
        campo_dudoso = any(
            cv.veredicto.status != EstadoVeredicto.verificado for cv in campos_verificados
        )
        campo_ilegible = any(
            cv.campo.status == EstadoCampo.ilegible for cv in campos_verificados
        )
        return campo_dudoso or campo_ilegible


class FichaVerificada(BaseModel):
    """Salida del sistema: ficha estructurada lista para confirmación humana.

    NUNCA se auto-confirma; siempre pasa por confirmación humana
    campo por campo (regla confirmacion-humana).
    No es diagnóstico ni indicación: refleja lo escrito, verificado.
    """

    receta_id: str
    medicamentos: list[MedicamentoVerificado]
    overall_confidence: float
    needs_review: bool

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def needs_review_consistente(self) -> "FichaVerificada":
        calculado = any(m.requiere_revision for m in self.medicamentos)
        if calculado and not self.needs_review:
            raise ValueError(
                "needs_review debe ser True cuando algún medicamento requiere revisión"
            )
        return self
