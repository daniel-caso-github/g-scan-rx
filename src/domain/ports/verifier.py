from abc import ABC, abstractmethod

from src.domain.entities.item_catalogo import ItemCatalogo
from src.domain.value_objects.campo_extraido import CampoExtraido
from src.domain.value_objects.dosis_normalizada import DosisNormalizada
from src.domain.value_objects.veredicto_verificacion import VeredictoVerificacion


class Verifier(ABC):
    """Port: verifica un campo extraído contra un ítem del catálogo.

    Nunca levanta excepción hacia el pipeline; degrada a VeredictoVerificacion.no_disponible()
    ante fallos de red o timeout.
    """

    @abstractmethod
    async def verify(
        self,
        farmaco: CampoExtraido,
        dosis: DosisNormalizada | None,
        candidate: ItemCatalogo,
    ) -> VeredictoVerificacion:
        ...
