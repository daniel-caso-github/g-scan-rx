import base64
import logging

from fastmcp import FastMCP

from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.domain.entities.prescription import Prescription
from src.domain.ports.anomaly_detector import AnomalyDetector
from src.domain.ports.retriever import Retriever

logger = logging.getLogger(__name__)


def build_mcp_server(
    extract_uc: ExtractPrescriptionUseCase,
    verify_uc: VerifyMedicationUseCase,
    retriever: Retriever,
    anomaly_detector: AnomalyDetector | None = None,
) -> FastMCP:
    mcp = FastMCP("gscan-rx")

    @mcp.tool()
    async def vision_extract(image_b64: str, image_hash: str) -> dict:
        """Extrae medicamentos de una imagen de receta médica.

        Devuelve una Prescription serializada con campos por medicamento
        (drug, dose, frequency, duration, route) y sus niveles de confianza.
        Campos ilegibles aparecen con status='unreadable' y value=null.
        """
        image_bytes = base64.b64decode(image_b64)
        prescription = await extract_uc.execute(image_bytes, image_hash)
        return prescription.model_dump()

    @mcp.tool()
    async def retrieve_drug(query: str, top_k: int = 5) -> list[dict]:
        """Recupera candidatos del catálogo oficial para un nombre de fármaco.

        Usa retrieval híbrido (BM25 + vector + reranker).
        Devuelve lista de {item, score} ordenada por relevancia descendente.
        """
        results = await retriever.retrieve(query, top_k=top_k)
        return [
            {"item": item.model_dump(), "score": score}
            for item, score in results
        ]

    @mcp.tool()
    async def verify_prescription(prescription_data: dict) -> dict:
        """Verifica cada medicamento de una Prescription contra el catálogo.

        Devuelve un VerifiedRecord con veredicto por campo (verified/uncertain/not_found)
        y un flag needs_review que indica si se requiere confirmación humana.
        """
        prescription = Prescription.model_validate(prescription_data)
        record = await verify_uc.execute(prescription)
        return record.model_dump()

    if anomaly_detector is not None:
        @mcp.tool()
        async def detect_anomaly(image_b64: str) -> dict:
            """Detecta si la imagen no es una receta médica (fuera de distribución).

            Devuelve {score, is_anomaly}. Score alto indica imagen OOD.
            Si is_anomaly es true, el agente debe abstenerse de procesar.
            """
            image_bytes = base64.b64decode(image_b64)
            score = await anomaly_detector.score(image_bytes)
            return {"score": score, "is_anomaly": score > 0.5}

    return mcp
