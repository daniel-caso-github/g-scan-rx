from abc import ABC, abstractmethod


class AnomalyDetector(ABC):
    """Port: detects images that are not medical prescriptions (OOD) via embeddings."""

    @abstractmethod
    async def score(self, image_bytes: bytes) -> float:
        """Returns anomaly score in [0.0, 1.0].

        High values indicate an out-of-distribution image (not a prescription).
        """
        ...
