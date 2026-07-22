import pytest

from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.domain.value_objects.verification_verdict import VerificationVerdict, VerdictStatus


class TestImageCrop:
    def test_creates_correctly(self):
        r = ImageCrop(bbox=(10, 20, 100, 30), crop_ref="test.png")
        assert r.bbox == (10, 20, 100, 30)

    def test_rejects_zero_width(self):
        with pytest.raises(ValueError):
            ImageCrop(bbox=(0, 0, 0, 30), crop_ref="x.png")

    def test_rejects_negative_coordinates(self):
        with pytest.raises(ValueError):
            ImageCrop(bbox=(-1, 0, 100, 30), crop_ref="x.png")

    def test_immutable(self, crop_dummy):
        with pytest.raises((TypeError, ValueError)):
            crop_dummy.crop_ref = "other.png"


class TestExtractedField:
    def test_readable_field(self, crop_dummy):
        f = ExtractedField(
            value="amoxicilina",
            confidence=0.9,
            status=FieldStatus.readable,
            source_crop=crop_dummy,
        )
        assert f.value == "amoxicilina"
        assert f.status == FieldStatus.readable

    def test_unreadable_requires_value_none(self, crop_dummy):
        with pytest.raises(ValueError):
            ExtractedField(
                value="algo",
                confidence=0.2,
                status=FieldStatus.unreadable,
                source_crop=crop_dummy,
            )

    def test_readable_requires_value(self, crop_dummy):
        with pytest.raises(ValueError):
            ExtractedField(
                value=None,
                confidence=0.9,
                status=FieldStatus.readable,
                source_crop=crop_dummy,
            )

    def test_confidence_out_of_range(self, crop_dummy):
        with pytest.raises(ValueError):
            ExtractedField(
                value="x",
                confidence=1.5,
                status=FieldStatus.readable,
                source_crop=crop_dummy,
            )

    def test_unreadable_field_correct(self, crop_dummy):
        f = ExtractedField(
            value=None,
            confidence=0.1,
            status=FieldStatus.unreadable,
            source_crop=crop_dummy,
        )
        assert f.value is None


class TestNormalizedDose:
    def test_creates_correctly(self):
        d = NormalizedDose(amount=500.0, unit="mg", frequency_hours=8.0, route="oral")
        assert d.amount == 500.0
        assert d.unit == "mg"

    def test_negative_amount_rejected(self):
        with pytest.raises(ValueError):
            NormalizedDose(amount=-10.0, unit="mg")

    def test_non_canonical_unit_rejected(self):
        with pytest.raises(ValueError):
            NormalizedDose(amount=500.0, unit="kilogramos")

    def test_non_canonical_route_rejected(self):
        with pytest.raises(ValueError):
            NormalizedDose(amount=500.0, unit="mg", route="intragástrica")

    def test_optional_fields_none(self):
        d = NormalizedDose(amount=20.0, unit="mg")
        assert d.frequency_hours is None
        assert d.route is None


class TestVerificationVerdict:
    def test_verified_requires_catalog_id(self):
        with pytest.raises(ValueError):
            VerificationVerdict(
                status=VerdictStatus.verified,
                catalog_item_id=None,
                match_score=0.95,
            )

    def test_uncertain_without_catalog_id(self):
        v = VerificationVerdict(status=VerdictStatus.uncertain, match_score=0.4)
        assert v.catalog_item_id is None

    def test_no_disponible(self):
        v = VerificationVerdict.no_disponible()
        assert v.status == VerdictStatus.uncertain
        assert "verificación no disponible" in v.notes

    def test_match_score_out_of_range(self):
        with pytest.raises(ValueError):
            VerificationVerdict(status=VerdictStatus.uncertain, match_score=1.5)
