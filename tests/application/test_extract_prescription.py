from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.normalized_dose import NormalizedDose

_CROP = ImageCrop(bbox=(0, 0, 100, 30), crop_ref="crop_0_0_100_30.png")

_READABLE_DOSE = ExtractedField(
    value="500 mg",
    confidence=0.95,
    status=FieldStatus.readable,
    source_crop=_CROP,
)

_READABLE_DRUG = ExtractedField(
    value="amoxicilina",
    confidence=0.97,
    status=FieldStatus.readable,
    source_crop=_CROP,
)

_READABLE_FREQ = ExtractedField(
    value="cada 8 horas",
    confidence=0.90,
    status=FieldStatus.readable,
    source_crop=_CROP,
)

_READABLE_DURATION = ExtractedField(
    value="7 dias",
    confidence=0.88,
    status=FieldStatus.readable,
    source_crop=_CROP,
)

_READABLE_ROUTE = ExtractedField(
    value="oral",
    confidence=0.92,
    status=FieldStatus.readable,
    source_crop=_CROP,
)


def _make_medication(dose: ExtractedField = _READABLE_DOSE) -> ExtractedMedication:
    return ExtractedMedication(
        drug=_READABLE_DRUG,
        dose=dose,
        frequency=_READABLE_FREQ,
        duration=_READABLE_DURATION,
        route=_READABLE_ROUTE,
        crop=_CROP,
    )


@pytest.fixture
def mock_extractor():
    extractor = MagicMock()
    extractor.extract = AsyncMock(return_value=[_make_medication(), _make_medication()])
    return extractor


@pytest.fixture
def mock_normalizer():
    normalizer = MagicMock()
    normalizer.normalize_dose = AsyncMock(
        return_value=NormalizedDose(amount=500.0, unit="mg")
    )
    return normalizer


@pytest.fixture
def use_case(mock_extractor, mock_normalizer):
    return ExtractPrescriptionUseCase(extractor=mock_extractor, normalizer=mock_normalizer)


async def test_execute_returns_prescription_with_medications(use_case):
    prescription = await use_case.execute(b"fake-image", "abc123")
    assert len(prescription.medications) == 2


async def test_execute_with_empty_extraction(mock_normalizer):
    extractor = MagicMock()
    extractor.extract = AsyncMock(return_value=[])
    uc = ExtractPrescriptionUseCase(extractor=extractor, normalizer=mock_normalizer)

    prescription = await uc.execute(b"fake-image", "abc123")

    assert prescription.medications == []
    assert prescription.status == "pending"


async def test_execute_normalizer_called_for_dose_fields(mock_extractor, mock_normalizer):
    uc = ExtractPrescriptionUseCase(extractor=mock_extractor, normalizer=mock_normalizer)
    await uc.execute(b"fake-image", "abc123")

    assert mock_normalizer.normalize_dose.call_count >= 1


async def test_execute_normalizer_failure_does_not_propagate(mock_extractor):
    normalizer = MagicMock()
    normalizer.normalize_dose = AsyncMock(return_value=None)
    uc = ExtractPrescriptionUseCase(extractor=mock_extractor, normalizer=normalizer)

    prescription = await uc.execute(b"fake-image", "abc123")

    assert len(prescription.medications) == 2


async def test_execute_prescription_has_correct_image_hash(use_case):
    image_hash = "deadbeef1234"
    prescription = await use_case.execute(b"fake-image", image_hash)

    assert prescription.image_hash == image_hash
