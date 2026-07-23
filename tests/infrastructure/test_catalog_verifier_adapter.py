
from src.domain.entities.catalog_item import CatalogItem
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.domain.value_objects.verification_verdict import VerdictStatus
from src.infrastructure.verification.catalog_verifier_adapter import CatalogVerifierAdapter

_CROP = ImageCrop(bbox=(0, 0, 10, 10), crop_ref="test")
_DRUG = ExtractedField(value="Amoxicilina", confidence=0.95, status=FieldStatus.readable, source_crop=_CROP)


def _item(dose_range=None) -> CatalogItem:
    return CatalogItem(
        id="item-1",
        active_ingredient="amoxicilina",
        presentation="capsulas",
        source="cima",
        dose_range=dose_range,
    )


async def test_dose_in_range_returns_verified():
    adapter = CatalogVerifierAdapter()
    dose = NormalizedDose(amount=500.0, unit="mg")
    item = _item({"min": 250.0, "max": 1000.0, "unit": "mg"})

    verdict = await adapter.verify(_DRUG, dose, item)

    assert verdict.status == VerdictStatus.verified
    assert verdict.catalog_item_id == "item-1"
    assert verdict.match_score == 1.0


async def test_dose_above_range_returns_uncertain():
    adapter = CatalogVerifierAdapter()
    dose = NormalizedDose(amount=2000.0, unit="mg")
    item = _item({"min": 250.0, "max": 1000.0, "unit": "mg"})

    verdict = await adapter.verify(_DRUG, dose, item)

    assert verdict.status == VerdictStatus.uncertain
    assert "fuera de rango" in verdict.notes[0]


async def test_none_dose_returns_uncertain():
    adapter = CatalogVerifierAdapter()
    item = _item({"min": 250.0, "max": 1000.0, "unit": "mg"})

    verdict = await adapter.verify(_DRUG, None, item)

    assert verdict.status == VerdictStatus.uncertain
    assert verdict.catalog_item_id == "item-1"


async def test_no_dose_range_in_catalog_returns_uncertain():
    adapter = CatalogVerifierAdapter()
    dose = NormalizedDose(amount=500.0, unit="mg")

    verdict = await adapter.verify(_DRUG, dose, _item())

    assert verdict.status == VerdictStatus.uncertain
    assert "sin rango" in verdict.notes[0]


async def test_unit_mismatch_returns_uncertain():
    adapter = CatalogVerifierAdapter()
    dose = NormalizedDose(amount=500.0, unit="mg")
    item = _item({"min": 0.5, "max": 1.0, "unit": "g"})

    verdict = await adapter.verify(_DRUG, dose, item)

    assert verdict.status == VerdictStatus.uncertain
    assert "unidad incompatible" in verdict.notes[0]


async def test_no_disponible_on_unexpected_error():
    class BrokenItem:
        id = "x"
        dose_range = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))

    adapter = CatalogVerifierAdapter()
    dose = NormalizedDose(amount=500.0, unit="mg")

    verdict = await adapter.verify(_DRUG, dose, BrokenItem())  # type: ignore[arg-type]

    assert verdict.status == VerdictStatus.uncertain
    assert "verificación no disponible" in verdict.notes
