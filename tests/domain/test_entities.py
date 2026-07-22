import pytest

from src.domain.entities.catalog_item import CatalogItem
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.services.make_id import make_id
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.verification_verdict import VerificationVerdict, VerdictStatus


@pytest.fixture
def crop():
    return ImageCrop(bbox=(0, 0, 100, 30), crop_ref="c.png")


@pytest.fixture
def readable_field(crop):
    return ExtractedField(value="amoxicilina", confidence=0.9, status=FieldStatus.readable, source_crop=crop)


@pytest.fixture
def unreadable_field(crop):
    return ExtractedField(value=None, confidence=0.1, status=FieldStatus.unreadable, source_crop=crop)


@pytest.fixture
def verified_verdict():
    return VerificationVerdict(
        status=VerdictStatus.verified,
        catalog_item_id="abc123",
        match_score=0.95,
    )


@pytest.fixture
def uncertain_verdict():
    return VerificationVerdict(status=VerdictStatus.uncertain, match_score=0.3)


@pytest.fixture
def catalog_item():
    return CatalogItem(
        id=make_id("cima", "amoxicilina", "cápsula 500 mg"),
        active_ingredient="amoxicilina",
        brand_name="Amoxil",
        presentation="cápsula 500 mg",
        source="cima",
    )


class TestCatalogItem:
    def test_invalid_source_rejected(self):
        with pytest.raises(ValueError):
            CatalogItem(
                id="x",
                active_ingredient="x",
                presentation="x",
                source="fda",
            )

    def test_empty_id_rejected(self):
        with pytest.raises(ValueError):
            CatalogItem(id="  ", active_ingredient="x", presentation="x", source="cima")

    def test_make_id_deterministic(self, catalog_item):
        id1 = make_id("cima", "amoxicilina", "cápsula 500 mg")
        id2 = make_id("cima", "amoxicilina", "cápsula 500 mg")
        assert id1 == id2


class TestPrescription:
    def test_empty_prescription(self):
        p = Prescription(id="p1", image_hash="abc123")
        assert p.medications == []
        assert p.status == PrescriptionStatus.pending

    def test_prescription_immutable(self):
        p = Prescription(id="p1", image_hash="abc")
        with pytest.raises((TypeError, ValueError)):
            p.status = PrescriptionStatus.confirmed


class TestVerifiedRecord:
    def _make_verified_field(self, field, verdict):
        return VerifiedField(field=field, verdict=verdict)

    def _make_verified_medication(self, readable_field, verified_verdict):
        vf = VerifiedField(field=readable_field, verdict=verified_verdict)
        return VerifiedMedication(
            drug=vf, dose=vf, frequency=vf, duration=vf, route=vf
        )

    def test_record_no_review_needed(self, readable_field, verified_verdict):
        med = self._make_verified_medication(readable_field, verified_verdict)
        record = VerifiedRecord(
            prescription_id="p1",
            medications=[med],
            overall_confidence=0.9,
            needs_review=False,
        )
        assert not record.needs_review

    def test_record_with_unreadable_field_requires_review(
        self, unreadable_field, readable_field, verified_verdict, uncertain_verdict
    ):
        vf_unreadable = VerifiedField(field=unreadable_field, verdict=uncertain_verdict)
        vf_readable = VerifiedField(field=readable_field, verdict=verified_verdict)
        med = VerifiedMedication(
            drug=vf_unreadable,
            dose=vf_readable,
            frequency=vf_readable,
            duration=vf_readable,
            route=vf_readable,
        )
        record = VerifiedRecord(
            prescription_id="p1",
            medications=[med],
            overall_confidence=0.5,
            needs_review=True,
        )
        assert record.needs_review

    def test_inconsistent_record_rejected(self, unreadable_field, readable_field, uncertain_verdict, verified_verdict):
        vf_unreadable = VerifiedField(field=unreadable_field, verdict=uncertain_verdict)
        vf_readable = VerifiedField(field=readable_field, verdict=verified_verdict)
        med = VerifiedMedication(
            drug=vf_unreadable, dose=vf_readable, frequency=vf_readable,
            duration=vf_readable, route=vf_readable,
        )
        with pytest.raises(ValueError):
            VerifiedRecord(
                prescription_id="p1",
                medications=[med],
                overall_confidence=0.5,
                needs_review=False,
            )
