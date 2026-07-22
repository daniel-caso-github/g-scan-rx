import logging

from src.domain.entities.catalog_item import CatalogItem
from src.domain.ports.verifier import Verifier
from src.domain.value_objects.extracted_field import ExtractedField
from src.domain.value_objects.normalized_dose import NormalizedDose
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict

logger = logging.getLogger(__name__)


class CatalogVerifierAdapter(Verifier):
    """Rule-based verifier: checks normalized dose against catalog dose_range.

    Never raises toward the pipeline; degrades to no_disponible() on unexpected errors.
    """

    async def verify(
        self,
        drug: ExtractedField,
        dose: NormalizedDose | None,
        candidate: CatalogItem,
    ) -> VerificationVerdict:
        try:
            return self._check(dose, candidate)
        except Exception:
            logger.warning("Error en CatalogVerifierAdapter; degradando a no_disponible")
            return VerificationVerdict.no_disponible()

    def _check(self, dose: NormalizedDose | None, candidate: CatalogItem) -> VerificationVerdict:
        if dose is None:
            return VerificationVerdict(
                status=VerdictStatus.uncertain,
                catalog_item_id=candidate.id,
                notes=["dosis no disponible para verificar rango"],
            )

        dose_range = candidate.dose_range
        if not dose_range:
            return VerificationVerdict(
                status=VerdictStatus.uncertain,
                catalog_item_id=candidate.id,
                notes=["catálogo sin rango de dosis definido"],
            )

        range_unit = dose_range.get("unit", "").lower().strip()
        if range_unit and dose.unit.lower() != range_unit:
            return VerificationVerdict(
                status=VerdictStatus.uncertain,
                catalog_item_id=candidate.id,
                notes=[f"unidad incompatible: extraída '{dose.unit}', catálogo '{range_unit}'"],
            )

        min_dose = dose_range.get("min")
        max_dose = dose_range.get("max")

        if min_dose is None or max_dose is None:
            return VerificationVerdict(
                status=VerdictStatus.uncertain,
                catalog_item_id=candidate.id,
                notes=["rango de dosis incompleto en catálogo"],
            )

        in_range = float(min_dose) <= dose.amount <= float(max_dose)
        return VerificationVerdict(
            status=VerdictStatus.verified if in_range else VerdictStatus.uncertain,
            catalog_item_id=candidate.id,
            match_score=1.0 if in_range else 0.3,
            notes=[] if in_range else [
                f"dosis {dose.amount} {dose.unit} fuera de rango [{min_dose}, {max_dose}]"
            ],
        )
