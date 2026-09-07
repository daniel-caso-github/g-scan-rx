from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from prometheus_client import REGISTRY

from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict
from src.interfaces.api.dependencies import get_verify_uc
from src.interfaces.api.routers import prescriptions

_CROP = ImageCrop(bbox=(0, 0, 10, 10), crop_ref="test")


def _field() -> ExtractedField:
    return ExtractedField(value="amoxicilina", confidence=0.9, status=FieldStatus.readable, source_crop=_CROP)


def _prescription_payload() -> dict:
    med = ExtractedMedication(
        drug=_field(), dose=_field(), frequency=_field(), duration=_field(), route=_field(), crop=_CROP
    )
    prescription = Prescription(
        id="rx-1", image_hash="abc123", medications=[med], status=PrescriptionStatus.pending
    )
    return prescription.model_dump(mode="json")


def _verified_record(status: VerdictStatus) -> VerifiedRecord:
    drug_verdict = VerificationVerdict(
        status=status, catalog_item_id="cat-1" if status == VerdictStatus.verified else None
    )
    other = VerifiedField(field=_field(), verdict=VerificationVerdict(status=VerdictStatus.uncertain))
    med = VerifiedMedication(
        drug=VerifiedField(field=_field(), verdict=drug_verdict),
        dose=other,
        frequency=other,
        duration=other,
        route=other,
    )
    return VerifiedRecord(prescription_id="rx-1", medications=[med], overall_confidence=0.9, needs_review=True)


def _make_app(verified_record: VerifiedRecord) -> FastAPI:
    app = FastAPI()
    app.include_router(prescriptions.router)
    use_case = MagicMock()
    use_case.execute = AsyncMock(return_value=verified_record)
    app.dependency_overrides[get_verify_uc] = lambda: use_case
    return app


def _count(status: str) -> float:
    return REGISTRY.get_sample_value("gscan_verdicts_total", {"status": status}) or 0.0


async def test_verify_endpoint_records_verdict_metric():
    before = _count("not_found")
    app = _make_app(_verified_record(VerdictStatus.not_found))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/verify", json=_prescription_payload())

    assert response.status_code == 200
    assert _count("not_found") == before + 1


async def test_dashboard_endpoint_returns_html():
    app = _make_app(_verified_record(VerdictStatus.verified))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/dashboard")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "G-Scan-RX" in response.text
