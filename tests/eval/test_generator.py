"""Tests for the synthetic prescription generator v1."""

from src.domain.entities.prescription import PrescriptionStatus
from src.domain.value_objects.extracted_field import FieldStatus


class TestPrescriptionGenerator:
    def test_generates_prescriptions(self, generator):
        prescriptions = generator.generate(n=5)
        assert len(prescriptions) == 5

    def test_prescription_has_medications(self, generator):
        prescriptions = generator.generate(n=3)
        for prescription in prescriptions:
            assert len(prescription.medications) >= 1

    def test_fields_have_crop(self, generator):
        prescriptions = generator.generate(n=3)
        for prescription in prescriptions:
            for med in prescription.medications:
                for f in (med.drug, med.dose, med.frequency, med.duration, med.route):
                    assert f.source_crop is not None

    def test_unreadable_has_value_none(self, generator):
        prescriptions = generator.generate(n=50)
        for prescription in prescriptions:
            for med in prescription.medications:
                for f in (med.drug, med.dose, med.frequency, med.duration, med.route):
                    if f.status == FieldStatus.unreadable:
                        assert f.value is None

    def test_prescription_status_pending(self, generator):
        prescription = generator.generate(n=1)[0]
        assert prescription.status == PrescriptionStatus.pending

    def test_ids_deterministic_with_same_seed(self, catalog):
        from src.data.synthetic.generator import PrescriptionGenerator

        gen1 = PrescriptionGenerator(catalog=catalog, seed=99)
        gen2 = PrescriptionGenerator(catalog=catalog, seed=99)
        p1 = gen1.generate(n=3)
        p2 = gen2.generate(n=3)
        assert [p.id for p in p1] == [p.id for p in p2]

    def test_ground_truth_has_prescription_id(self, generator):
        prescriptions = generator.generate(n=3)
        gt = generator.generate_ground_truth(prescriptions)
        prescription_ids = {p.id for p in prescriptions}
        for entry in gt:
            assert entry["prescription_id"] in prescription_ids
