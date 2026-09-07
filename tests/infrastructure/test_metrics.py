from prometheus_client import REGISTRY

from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict
from src.infrastructure.observability.metrics import record_verdicts

_CROP = ImageCrop(bbox=(0, 0, 10, 10), crop_ref="test")


def _field() -> ExtractedField:
    return ExtractedField(value="amoxicilina", confidence=0.9, status=FieldStatus.readable, source_crop=_CROP)


def _other_field(status=VerdictStatus.uncertain) -> VerifiedField:
    return VerifiedField(field=_field(), verdict=VerificationVerdict(status=status))


def _record_with_drug_status(status: VerdictStatus) -> VerifiedRecord:
    drug_verdict = VerificationVerdict(
        status=status, catalog_item_id="cat-1" if status == VerdictStatus.verified else None
    )
    med = VerifiedMedication(
        drug=VerifiedField(field=_field(), verdict=drug_verdict),
        dose=_other_field(),
        frequency=_other_field(),
        duration=_other_field(),
        route=_other_field(),
    )
    return VerifiedRecord(
        prescription_id="rx-1", medications=[med], overall_confidence=0.9, needs_review=True
    )


def _count(status: str) -> float:
    return REGISTRY.get_sample_value("gscan_verdicts_total", {"status": status}) or 0.0


def test_record_verdicts_increments_counter_for_verified_drug():
    before = _count("verified")
    record_verdicts(_record_with_drug_status(VerdictStatus.verified))
    assert _count("verified") == before + 1


def test_record_verdicts_counts_not_found_as_hallucination_proxy():
    before = _count("not_found")
    record_verdicts(_record_with_drug_status(VerdictStatus.not_found))
    assert _count("not_found") == before + 1


def test_record_verdicts_only_counts_drug_field_not_other_fields():
    """Other fields (dose/frequency/...) aren't checked against the catalog the same way; only
    the drug verdict is a hallucination proxy."""
    before_uncertain = _count("uncertain")
    record_verdicts(_record_with_drug_status(VerdictStatus.verified))
    assert _count("uncertain") == before_uncertain
