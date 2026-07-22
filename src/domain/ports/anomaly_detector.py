from abc import ABC, abstractmethod


class AnomalyDetector(ABC):
    """Port: detecta imágenes que no son recetas médicas (OOD) via embeddings."""

    @abstractmethod
    async def score(self, image_bytes: bytes) -> float:
        """Devuelve puntuación de anomalía en [0.0, 1.0].

        Valores altos indican imagen fuera de distribución (no es una receta).
        """
        ...
