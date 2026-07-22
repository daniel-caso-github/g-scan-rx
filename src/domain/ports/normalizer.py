from abc import ABC, abstractmethod

from src.domain.value_objects.campo_extraido import CampoExtraido
from src.domain.value_objects.dosis_normalizada import DosisNormalizada


class Normalizer(ABC):
    """Port: normaliza texto crudo extraído por el VLM a estructuras canónicas."""

    @abstractmethod
    async def normalize_dosis(self, campo: CampoExtraido) -> DosisNormalizada | None:
        """Convierte texto de dosis a unidades canónicas.

        Devuelve None si no se puede normalizar con confianza suficiente;
        el caller marca el campo como dudoso.
        """
        ...
