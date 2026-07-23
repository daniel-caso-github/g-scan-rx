from unittest.mock import AsyncMock, MagicMock

from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.domain.entities.catalog_item import CatalogItem
from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict

_CROP = ImageCrop(bbox=(0, 0, 100, 30), crop_ref="test")


def _field(value="amoxicilina", status=FieldStatus.readable, confidence=0.95) -> ExtractedField:
    return ExtractedField(value=value, confidence=confidence, status=status, source_crop=_CROP)


def _unreadable_field() -> ExtractedField:
    return ExtractedField(value=None, confidence=0.0, status=FieldStatus.unreadable, source_crop=_CROP)


def _medication(drug_value="amoxicilina", drug_status=FieldStatus.readable) -> ExtractedMedication:
    return ExtractedMedication(
        drug=_field(drug_value, drug_status),
        dose=_field("500mg"),
        frequency=_field("cada 8h"),
        duration=_field("7 días"),
        route=_field("oral"),
        crop=_CROP,
    )


def _prescription(medications=None) -> Prescription:
    return Prescription(
        id="rx-001",
        image_hash="abc123",
        medications=[_medication()] if medications is None else medications,
        status=PrescriptionStatus.pending,
    )


def _catalog_item() -> CatalogItem:
    return CatalogItem(
        id="cat-1",
        active_ingredient="amoxicilina",
        presentation="capsulas",
        source="cima",
        dose_range={"min": 250.0, "max": 1000.0, "unit": "mg"},
    )


def _make_use_case(retrieval_result=None, normalize_result=None, verify_result=None):
    retriever = MagicMock()
    retriever.retrieve = AsyncMock(
        return_value=[(_catalog_item(), 0.85)] if retrieval_result is None else retrieval_result
    )
    normalizer = MagicMock()
    normalizer.normalize_dose = AsyncMock(
        return_value=normalize_result or NormalizedDose(amount=500.0, unit="mg")
    )
    verifier = MagicMock()
    verifier.verify = AsyncMock(
        return_value=verify_result or VerificationVerdict(
            status=VerdictStatus.verified, catalog_item_id="cat-1", match_score=1.0
        )
    )
    return VerifyMedicationUseCase(retriever=retriever, normalizer=normalizer, verifier=verifier)


async def test_returns_verified_record():
    uc = _make_use_case()
    record = await uc.execute(_prescription())
    assert record.prescription_id == "rx-001"
    assert len(record.medications) == 1


async def test_drug_verdict_verified_when_score_above_threshold():
    uc = _make_use_case()
    record = await uc.execute(_prescription())
    assert record.medications[0].drug.verdict.status == VerdictStatus.verified


async def test_drug_verdict_uncertain_when_score_below_verified_threshold():
    uc = _make_use_case(retrieval_result=[(_catalog_item(), 0.5)])
    record = await uc.execute(_prescription())
    assert record.medications[0].drug.verdict.status == VerdictStatus.uncertain


async def test_drug_verdict_not_found_when_no_results():
    uc = _make_use_case(retrieval_result=[])
    record = await uc.execute(_prescription())
    assert record.medications[0].drug.verdict.status == VerdictStatus.not_found
    assert record.medications[0].catalog_match is None


async def test_unreadable_drug_skips_retrieval():
    uc = _make_use_case()
    med = ExtractedMedication(
        drug=_unreadable_field(),
        dose=_field("500mg"),
        frequency=_field("cada 8h"),
        duration=_field("7 días"),
        route=_field("oral"),
        crop=_CROP,
    )
    record = await uc.execute(_prescription([med]))
    uc._retriever.retrieve.assert_not_awaited()
    assert record.medications[0].drug.verdict.status == VerdictStatus.not_found


async def test_needs_review_true_when_uncertain_field():
    uc = _make_use_case(
        retrieval_result=[(_catalog_item(), 0.5)],
        verify_result=VerificationVerdict(status=VerdictStatus.uncertain, catalog_item_id="cat-1"),
    )
    record = await uc.execute(_prescription())
    assert record.needs_review is True


async def test_empty_prescription_returns_needs_review():
    uc = _make_use_case()
    record = await uc.execute(_prescription([]))
    assert record.needs_review is True
    assert record.medications == []


async def test_overall_confidence_is_mean_of_field_confidences():
    uc = _make_use_case()
    record = await uc.execute(_prescription())
    assert 0.0 < record.overall_confidence <= 1.0


async def test_normalizer_not_called_for_unreadable_dose():
    med = ExtractedMedication(
        drug=_field("amoxicilina"),
        dose=_unreadable_field(),
        frequency=_field("cada 8h"),
        duration=_field("7 días"),
        route=_field("oral"),
        crop=_CROP,
    )
    uc = _make_use_case()
    await uc.execute(_prescription([med]))
    uc._normalizer.normalize_dose.assert_not_awaited()
