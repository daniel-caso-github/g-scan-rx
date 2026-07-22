import hashlib
import logging

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.application.agent.react_loop import AgentAbstainError, ReActLoop
from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.config import settings
from src.domain.entities.prescription import Prescription
from src.domain.entities.verified_record import VerifiedRecord
from src.domain.ports.guardrail import Guardrail
from src.domain.ports.image_cache import ImageCache
from src.infrastructure.observability.metrics import ABSTENTIONS_TOTAL, CACHE_HITS_TOTAL, EXTRACTIONS_TOTAL
from src.interfaces.api.dependencies import (
    get_extract_uc,
    get_image_cache,
    get_injection_guardrail,
    get_pii_guardrail,
    get_react_loop,
    get_verify_uc,
)
from src.interfaces.api.schemas import ApiResponse, HealthResponse

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["prescriptions"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.post("/extract", response_model=ApiResponse[Prescription])
@limiter.limit(settings.rate_limit_extract)
async def extract(
    request: Request,
    file: UploadFile = File(...),
    use_case: ExtractPrescriptionUseCase = Depends(get_extract_uc),
    pii_guardrail: Guardrail = Depends(get_pii_guardrail),
    injection_guardrail: Guardrail = Depends(get_injection_guardrail),
    image_cache: ImageCache = Depends(get_image_cache),
) -> ApiResponse[Prescription]:
    try:
        image_bytes = await file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        cached = await image_cache.get(image_hash)
        if cached is not None:
            CACHE_HITS_TOTAL.inc()
            EXTRACTIONS_TOTAL.labels(result="cache_hit").inc()
            return ApiResponse.ok(cached)

        prescription = await use_case.execute(image_bytes, image_hash)

        extracted_text = " ".join(
            str(med.drug.value) for med in prescription.medications if med.drug.value
        )
        if extracted_text:
            inj_result = await injection_guardrail.check(extracted_text)
            if not inj_result.passed:
                EXTRACTIONS_TOTAL.labels(result="injection_blocked").inc()
                return ApiResponse.fail(
                    code="INJECTION_DETECTED",
                    message="Contenido adversario detectado en la imagen",
                )
            pii_result = await pii_guardrail.check(extracted_text)
            if not pii_result.passed:
                logger.error("PII detectado en extracción, respuesta bloqueada; image_hash=%s", image_hash)
                EXTRACTIONS_TOTAL.labels(result="pii_blocked").inc()
                return ApiResponse.fail(
                    code="PII_DETECTED",
                    message="La imagen contiene datos personales identificables; no se puede procesar",
                )

        await image_cache.set(image_hash, prescription)
        EXTRACTIONS_TOTAL.labels(result="success").inc()
        return ApiResponse.ok(prescription)
    except Exception:
        EXTRACTIONS_TOTAL.labels(result="error").inc()
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
@limiter.limit(settings.rate_limit_process)
async def process(
    request: Request,
    file: UploadFile = File(...),
    loop: ReActLoop = Depends(get_react_loop),
) -> ApiResponse[VerifiedRecord]:
    try:
        image_bytes = await file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        record = await loop.execute(image_bytes, image_hash)
        return ApiResponse.ok(record)
    except AgentAbstainError as exc:
        ABSTENTIONS_TOTAL.inc()
        return ApiResponse.fail(code="IMAGE_OOD", message=str(exc))
    except Exception:
        logger.exception("Error en /process")
        return ApiResponse.fail(code="PROCESS_ERROR", message="Error interno al procesar la receta")
