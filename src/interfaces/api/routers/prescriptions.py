import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.application.agent.react_loop import AgentAbstainError, ReActLoop
from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.domain.entities.prescription import Prescription
from src.domain.entities.verified_record import VerifiedRecord
from src.interfaces.api.dependencies import get_extract_uc, get_react_loop, get_verify_uc
from src.interfaces.api.schemas import HealthResponse

router = APIRouter(tags=["prescriptions"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/extract", response_model=Prescription)
async def extract(
    file: UploadFile = File(...),
    use_case: ExtractPrescriptionUseCase = Depends(get_extract_uc),
) -> Prescription:
    image_bytes = await file.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    return await use_case.execute(image_bytes, image_hash)


@router.post("/verify", response_model=VerifiedRecord)
async def verify(
    prescription: Prescription,
    use_case: VerifyMedicationUseCase = Depends(get_verify_uc),
) -> VerifiedRecord:
    return await use_case.execute(prescription)


@router.post("/process", response_model=VerifiedRecord)
async def process(
    file: UploadFile = File(...),
    loop: ReActLoop = Depends(get_react_loop),
) -> VerifiedRecord:
    image_bytes = await file.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    try:
        return await loop.execute(image_bytes, image_hash)
    except AgentAbstainError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
