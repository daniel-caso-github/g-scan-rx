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
        """Extract medications from a handwritten prescription image.

        Returns a serialized Prescription with per-medication fields
        (drug, dose, frequency, duration, route) and their confidence levels.
        Unreadable fields appear with status='unreadable' and value=null.
        """
        image_bytes = base64.b64decode(image_b64)
        prescription = await extract_uc.execute(image_bytes, image_hash)
        return prescription.model_dump()

    @mcp.tool()
    async def retrieve_drug(query: str, top_k: int = 5) -> list[dict]:
        """Retrieve candidates from the official catalog for a drug name.

        Uses hybrid retrieval (BM25 + vector + reranker).
        Returns a list of {item, score} sorted by descending relevance.
        """
        results = await retriever.retrieve(query, top_k=top_k)
        return [
            {"item": item.model_dump(), "score": score}
            for item, score in results
        ]

    @mcp.tool()
    async def verify_prescription(prescription_data: dict) -> dict:
        """Verify each medication in a Prescription against the official catalog.

        Returns a VerifiedRecord with a per-field verdict (verified/uncertain/not_found)
        and a needs_review flag indicating whether human confirmation is required.
        """
        prescription = Prescription.model_validate(prescription_data)
        record = await verify_uc.execute(prescription)
        return record.model_dump()

    if anomaly_detector is not None:
        @mcp.tool()
        async def detect_anomaly(image_b64: str) -> dict:
            """Detect whether the image is not a medical prescription (out-of-distribution).

            Returns {score, is_anomaly}. High score indicates OOD image.
            If is_anomaly is true, the agent must abstain from processing.
            """
            image_bytes = base64.b64decode(image_b64)
            score = await anomaly_detector.score(image_bytes)
            return {"score": score, "is_anomaly": score > 0.5}

    return mcp
