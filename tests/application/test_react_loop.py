import base64
from unittest.mock import AsyncMock

import pytest

from src.application.agent.react_loop import AgentAbstainError, ReActLoop
from src.domain.entities.catalog_item import CatalogItem
from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict

_CROP = ImageCrop(bbox=(0, 0, 100, 30), crop_ref="test")
_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n"
_IMAGE_B64 = base64.b64encode(_IMAGE_BYTES).decode()
_IMAGE_HASH = "abc123"


def _field(value="amoxicilina") -> ExtractedField:
    return ExtractedField(value=value, confidence=0.95, status=FieldStatus.readable, source_crop=_CROP)


def _prescription_dict() -> dict:
    med = ExtractedMedication(
        drug=_field("amoxicilina"),
        dose=_field("500mg"),
        frequency=_field("cada 8h"),
        duration=_field("7 días"),
        route=_field("oral"),
        crop=_CROP,
    )
    return Prescription(
        id="rx-001",
        image_hash=_IMAGE_HASH,
        medications=[med],
        status=PrescriptionStatus.pending,
    ).model_dump()


def _verified_record_dict(needs_review: bool = False) -> dict:
    vf = VerifiedField(
        field=_field(),
        verdict=VerificationVerdict(
            status=VerdictStatus.verified,
            catalog_item_id="cat-1",
            match_score=1.0,
        ),
    )
    med = VerifiedMedication(
        drug=vf, dose=vf, frequency=vf, duration=vf, route=vf,
        catalog_match=CatalogItem(
            id="cat-1", active_ingredient="amoxicilina",
            presentation="capsulas", source="cima",
        ),
    )
    return VerifiedRecord(
        prescription_id="rx-001",
        medications=[med],
        overall_confidence=0.95,
        needs_review=needs_review,
    ).model_dump()


def _make_loop(anomaly_score=None, prescription=None, record=None):
    vision_extract = AsyncMock(return_value=prescription or _prescription_dict())
    retrieve_drug = AsyncMock(return_value=[])
    verify_prescription = AsyncMock(return_value=record or _verified_record_dict())
    detect_anomaly = None
    if anomaly_score is not None:
        detect_anomaly = AsyncMock(
            return_value={"score": anomaly_score, "is_anomaly": anomaly_score > 0.5}
        )
    loop = ReActLoop(
        vision_extract=vision_extract,
        retrieve_drug=retrieve_drug,
        verify_prescription=verify_prescription,
        detect_anomaly=detect_anomaly,
    )
    return loop, vision_extract, retrieve_drug, verify_prescription, detect_anomaly


async def test_happy_path_returns_verified_record():
    loop, *_ = _make_loop()
    record = await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    assert record.prescription_id == "rx-001"
    assert record.needs_review is False


async def test_steps_without_anomaly_detector_are_extract_then_verify():
    loop, vision_extract, _, verify_prescription, _ = _make_loop()
    await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    vision_extract.assert_awaited_once()
    verify_prescription.assert_awaited_once()


async def test_steps_with_anomaly_detector_are_detect_extract_verify():
    loop, vision_extract, _, verify_prescription, detect_anomaly = _make_loop(anomaly_score=0.1)
    await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    detect_anomaly.assert_awaited_once()
    vision_extract.assert_awaited_once()
    verify_prescription.assert_awaited_once()


async def test_anomaly_detected_raises_abstain_error():
    loop, *_ = _make_loop(anomaly_score=0.9)
    with pytest.raises(AgentAbstainError):
        await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)


async def test_anomaly_detected_skips_extract_and_verify():
    loop, vision_extract, _, verify_prescription, detect_anomaly = _make_loop(anomaly_score=0.9)
    with pytest.raises(AgentAbstainError):
        await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    detect_anomaly.assert_awaited_once()
    vision_extract.assert_not_awaited()
    verify_prescription.assert_not_awaited()


async def test_vision_extract_receives_correct_base64():
    loop, vision_extract, *_ = _make_loop()
    await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    call_kwargs = vision_extract.call_args.kwargs
    assert call_kwargs["image_b64"] == _IMAGE_B64
    assert call_kwargs["image_hash"] == _IMAGE_HASH


async def test_verify_receives_prescription_from_extract():
    loop, _, _, verify_prescription, _ = _make_loop()
    await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    call_kwargs = verify_prescription.call_args.kwargs
    assert call_kwargs["prescription_data"]["id"] == "rx-001"


async def test_needs_review_propagated_from_record():
    loop, *_ = _make_loop(record=_verified_record_dict(needs_review=True))
    record = await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
    assert record.needs_review is True


async def test_max_steps_guard_raises_runtime_error():
    vision_extract = AsyncMock(return_value=_prescription_dict())
    retrieve_drug = AsyncMock(return_value=[])
    verify_prescription = AsyncMock(side_effect=RuntimeError("fallo persistente"))
    loop = ReActLoop(
        vision_extract=vision_extract,
        retrieve_drug=retrieve_drug,
        verify_prescription=verify_prescription,
        max_steps=3,
    )
    with pytest.raises(RuntimeError):
        await loop.execute(_IMAGE_BYTES, _IMAGE_HASH)
