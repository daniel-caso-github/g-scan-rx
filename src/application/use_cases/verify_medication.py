import logging

from src.domain.entities.prescription import Prescription
from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.ports.normalizer import Normalizer
from src.domain.ports.retriever import Retriever
from src.domain.ports.verifier import Verifier
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict

logger = logging.getLogger(__name__)


class VerifyMedicationUseCase:
    def __init__(
        self,
        retriever: Retriever,
        normalizer: Normalizer,
        verifier: Verifier,
        verified_score: float = 0.7,
        uncertain_score: float = 0.3,
    ) -> None:
        self._retriever = retriever
        self._normalizer = normalizer
        self._verifier = verifier
        self._verified_score = verified_score
        self._uncertain_score = uncertain_score

    async def execute(self, prescription: Prescription) -> VerifiedRecord:
        verified_meds = []
        for med in prescription.medications:
            try:
                verified_med = await self._verify_one(med)
            except Exception:
                logger.warning("Error al verificar medicamento; se marca como necesita revisión")
                verified_med = self._fallback_medication(med)
            verified_meds.append(verified_med)

        needs_review = any(m.needs_review for m in verified_meds)
        overall_confidence = self._mean_confidence(verified_meds)

        return VerifiedRecord(
            prescription_id=prescription.id,
            medications=verified_meds,
            overall_confidence=overall_confidence,
            needs_review=needs_review or not verified_meds,
        )

    async def _verify_one(self, med) -> VerifiedMedication:
        from src.domain.entities.catalog_item import CatalogItem

        normalized_dose = None
        if med.dose.status != FieldStatus.unreadable and med.dose.value:
            normalized_dose = await self._normalizer.normalize_dose(med.dose)

        candidate: CatalogItem | None = None
        retrieval_score = 0.0
        if med.drug.status != FieldStatus.unreadable and med.drug.value:
            results = await self._retriever.retrieve(med.drug.value, top_k=1)
            if results:
                candidate, retrieval_score = results[0]

        drug_verdict = self._score_to_verdict(candidate, retrieval_score)

        if candidate is not None:
            dose_verdict = await self._verifier.verify(med.drug, normalized_dose, candidate)
        else:
            dose_verdict = self._status_verdict(med.dose, candidate)

        return VerifiedMedication(
            drug=VerifiedField(field=med.drug, verdict=drug_verdict),
            dose=VerifiedField(field=med.dose, verdict=dose_verdict),
            frequency=VerifiedField(field=med.frequency, verdict=self._status_verdict(med.frequency, candidate)),
            duration=VerifiedField(field=med.duration, verdict=self._status_verdict(med.duration, candidate)),
            route=VerifiedField(field=med.route, verdict=self._status_verdict(med.route, candidate)),
            catalog_match=candidate,
        )

    def _score_to_verdict(self, candidate, score: float) -> VerificationVerdict:
        if candidate is None:
            return VerificationVerdict(status=VerdictStatus.not_found)
        if score >= self._verified_score:
            return VerificationVerdict(
                status=VerdictStatus.verified,
                catalog_item_id=candidate.id,
                match_score=score,
            )
        if score >= self._uncertain_score:
            return VerificationVerdict(
                status=VerdictStatus.uncertain,
                catalog_item_id=candidate.id,
                match_score=score,
            )
        return VerificationVerdict(status=VerdictStatus.not_found)

    def _status_verdict(self, field: ExtractedField, candidate) -> VerificationVerdict:
        if field.status == FieldStatus.unreadable:
            return VerificationVerdict(status=VerdictStatus.not_found)
        return VerificationVerdict(
            status=VerdictStatus.uncertain,
            catalog_item_id=candidate.id if candidate else None,
        )

    def _fallback_medication(self, med) -> VerifiedMedication:
        not_found = VerificationVerdict(status=VerdictStatus.not_found)
        return VerifiedMedication(
            drug=VerifiedField(field=med.drug, verdict=not_found),
            dose=VerifiedField(field=med.dose, verdict=not_found),
            frequency=VerifiedField(field=med.frequency, verdict=not_found),
            duration=VerifiedField(field=med.duration, verdict=not_found),
            route=VerifiedField(field=med.route, verdict=not_found),
            catalog_match=None,
        )

    @staticmethod
    def _mean_confidence(meds: list[VerifiedMedication]) -> float:
        if not meds:
            return 0.0
        scores = [
            vf.field.confidence
            for m in meds
            for vf in [m.drug, m.dose, m.frequency, m.duration, m.route]
        ]
        return sum(scores) / len(scores)
