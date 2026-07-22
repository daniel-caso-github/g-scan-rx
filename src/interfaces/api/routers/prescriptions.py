import hashlib
import logging

from fastapi import APIRouter, Depends, File, UploadFile

logger = logging.getLogger(__name__)

from src.application.agent.react_loop import AgentAbstainError, ReActLoop
from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.domain.entities.prescription import Prescription
from src.domain.entities.verified_record import VerifiedRecord
from src.interfaces.api.dependencies import get_extract_uc, get_react_loop, get_verify_uc
from src.interfaces.api.schemas import ApiResponse, HealthResponse

router = APIRouter(tags=["prescriptions"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/extract", response_model=ApiResponse[Prescription])
async def extract(
    file: UploadFile = File(...),
    use_case: ExtractPrescriptionUseCase = Depends(get_extract_uc),
) -> ApiResponse[Prescription]:
    try:
        image_bytes = await file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        prescription = await use_case.execute(image_bytes, image_hash)
        return ApiResponse.ok(prescription)
    except Exception:
        logger.exception("Error en /extract")
        return ApiResponse.fail(code="EXTRACTION_ERROR", message="Error interno al extraer la receta")


@router.post("/verify", response_model=ApiResponse[VerifiedRecord])
async def verify(
    prescription: Prescription,
    use_case: VerifyMedicationUseCase = Depends(get_verify_uc),
) -> ApiResponse[VerifiedRecord]:
    try:
        record = await use_case.execute(prescription)
        return ApiResponse.ok(record)
    except Exception:
        logger.exception("Error en /verify")
        return ApiResponse.fail(code="VERIFICATION_ERROR", message="Error interno al verificar la receta")


@router.post("/process", response_model=ApiResponse[VerifiedRecord])
async def process(
    file: UploadFile = File(...),
    loop: ReActLoop = Depends(get_react_loop),
) -> ApiResponse[VerifiedRecord]:
    try:
        image_bytes = await file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        record = await loop.execute(image_bytes, image_hash)
        return ApiResponse.ok(record)
    except AgentAbstainError as exc:
        return ApiResponse.fail(code="IMAGE_OOD", message=str(exc))
    except Exception:
        logger.exception("Error en /process")
        return ApiResponse.fail(code="PROCESS_ERROR", message="Error interno al procesar la receta")
