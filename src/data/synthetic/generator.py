"""Synthetic prescription generator v1.

Generates ExtractedMedication and Prescription instances from the seed catalog.
Produces plausible text with variable confidence to simulate reading errors.

Usage:
    from src.data.synthetic.generator import PrescriptionGenerator
    from src.data.synthetic.catalog_seed import get_seed_catalog

    gen = PrescriptionGenerator(catalog=get_seed_catalog(), seed=42)
    prescriptions = gen.generate(n=10)
"""

import hashlib
import random
from typing import Any

from src.domain.entities.catalog_item import CatalogItem
from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.services.make_id import make_id
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop

_FREQUENCIES = [
    "cada 8 horas",
    "cada 12 horas",
    "cada 24 horas",
    "dos veces al día",
    "tres veces al día",
    "una vez al día",
]

_DURATIONS = [
    "5 días",
    "7 días",
    "10 días",
    "14 días",
    "1 mes",
    "2 semanas",
]

_ROUTES = ["oral", "tópica", "inhalatoria", "sublingual"]

_DEGRADATIONS = {
    "typographic": {
        "amoxicilina": ["amoxicilína", "amoxicilin", "amoxiciIina"],
        "ibuprofeno": ["ibuprofebo", "ibuprofen", "ibuprofeno"],
        "paracetamol": ["paracetanol", "paracetamol", "paracetmol"],
        "omeprazol": ["omeprazole", "omeprazol", "omeprazole"],
        "metformina": ["metfornina", "metformína", "metfomina"],
        "atorvastatina": ["atorvastatína", "atorvastina", "atrovastatina"],
        "losartan": ["lozartan", "losartan", "losartán"],
        "azitromicina": ["azitromicína", "azitromicina", "azitromiicna"],
    }
}


class PrescriptionGenerator:
    """Generates synthetic fictional prescriptions from a seed catalog."""

    def __init__(self, catalog: list[CatalogItem], seed: int = 0) -> None:
        self.catalog = catalog
        self._rng = random.Random(seed)

    def generate(self, n: int = 1) -> list[Prescription]:
        return [self._generate_prescription(i) for i in range(n)]

    def generate_medications(self, n: int = 1) -> list[ExtractedMedication]:
        return [self._generate_medication() for _ in range(n)]

    def _generate_prescription(self, idx: int) -> Prescription:
        n_medications = self._rng.randint(1, 3)
        medications = [self._generate_medication() for _ in range(n_medications)]
        image_hash = hashlib.sha256(f"synthetic-{idx}".encode()).hexdigest()
        return Prescription(
            id=make_id("synthetic", str(idx)),
            image_hash=image_hash,
            medications=medications,
            status=PrescriptionStatus.pending,
        )

    def _generate_medication(self) -> ExtractedMedication:
        item = self._rng.choice(self.catalog)
        line_crop = self._random_crop()

        drug = self._drug_field(item, line_crop)
        dose = self._dose_field(item, self._random_crop())
        frequency = self._text_field(
            self._rng.choice(_FREQUENCIES), self._random_crop()
        )
        duration = self._text_field(
            self._rng.choice(_DURATIONS), self._random_crop()
        )
        route = self._text_field(self._rng.choice(_ROUTES), self._random_crop())

        return ExtractedMedication(
            drug=drug,
            dose=dose,
            frequency=frequency,
            duration=duration,
            route=route,
            crop=line_crop,
        )

    def _drug_field(self, item: CatalogItem, crop: ImageCrop) -> ExtractedField:
        r = self._rng.random()
        base_name = item.active_ingredient

        if r < 0.05:
            return ExtractedField(
                value=None,
                confidence=self._rng.uniform(0.0, 0.35),
                status=FieldStatus.unreadable,
                source_crop=crop,
            )

        if r < 0.20:
            degraded = _DEGRADATIONS["typographic"].get(base_name, [base_name])
            value = self._rng.choice(degraded)
            return ExtractedField(
                value=value,
                confidence=self._rng.uniform(0.40, 0.65),
                status=FieldStatus.uncertain,
                source_crop=crop,
            )

        return ExtractedField(
            value=base_name,
            confidence=self._rng.uniform(0.75, 1.0),
            status=FieldStatus.readable,
            source_crop=crop,
        )

    def _dose_field(self, item: CatalogItem, crop: ImageCrop) -> ExtractedField:
        r = self._rng.random()
        concentration = item.concentration or "500 mg"

        if r < 0.05:
            return ExtractedField(
                value=None,
                confidence=self._rng.uniform(0.0, 0.35),
                status=FieldStatus.unreadable,
                source_crop=crop,
            )

        if r < 0.15:
            parts = concentration.split()
            if len(parts) >= 2:
                try:
                    num = float(parts[0])
                    wrong_value = f"{num * 10:.0f} {parts[1]}"
                except ValueError:
                    wrong_value = concentration
            else:
                wrong_value = concentration
            return ExtractedField(
                value=wrong_value,
                confidence=self._rng.uniform(0.40, 0.60),
                status=FieldStatus.uncertain,
                source_crop=crop,
            )

        return ExtractedField(
            value=concentration,
            confidence=self._rng.uniform(0.75, 1.0),
            status=FieldStatus.readable,
            source_crop=crop,
        )

    def _text_field(self, value: str, crop: ImageCrop) -> ExtractedField:
        r = self._rng.random()
        if r < 0.05:
            return ExtractedField(
                value=None,
                confidence=self._rng.uniform(0.0, 0.35),
                status=FieldStatus.unreadable,
                source_crop=crop,
            )
        confidence = self._rng.uniform(0.65, 1.0)
        status = FieldStatus.readable if confidence >= 0.7 else FieldStatus.uncertain
        return ExtractedField(
            value=value,
            confidence=confidence,
            status=status,
            source_crop=crop,
        )

    def _random_crop(self) -> ImageCrop:
        x = self._rng.randint(0, 400)
        y = self._rng.randint(0, 600)
        w = self._rng.randint(100, 500)
        h = self._rng.randint(20, 60)
        return ImageCrop(bbox=(x, y, w, h), crop_ref=f"crop_{x}_{y}_{w}_{h}.png")

    def generate_ground_truth(self, prescriptions: list[Prescription]) -> list[dict[str, Any]]:
        """Generates ground-truth annotations from known synthetic prescriptions.

        Only valid for prescriptions created by this generator (correct values
        are known because we generated them). For the real golden set
        (human handwriting), annotations are loaded from tests/fixtures/golden_set/.
        """
        ground_truth = []
        for prescription in prescriptions:
            for med in prescription.medications:
                ground_truth.append({
                    "prescription_id": prescription.id,
                    "drug": med.drug.value,
                    "dose": med.dose.value,
                    "frequency": med.frequency.value,
                    "duration": med.duration.value,
                    "route": med.route.value,
                })
        return ground_truth
