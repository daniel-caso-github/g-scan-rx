from pydantic import BaseModel, model_validator

from src.domain.entities.catalog_item import CatalogItem
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict


class VerifiedField(BaseModel):
    """Extracted field paired with its verification verdict against the catalog."""

    field: ExtractedField
    verdict: VerificationVerdict

    model_config = {"frozen": True}


class VerifiedMedication(BaseModel):
    """Medication with all fields verified against the catalog."""

    drug: VerifiedField
    dose: VerifiedField
    frequency: VerifiedField
    duration: VerifiedField
    route: VerifiedField
    catalog_match: CatalogItem | None = None

    model_config = {"frozen": True}

    @property
    def needs_review(self) -> bool:
        verified_fields = [self.drug, self.dose, self.frequency, self.duration, self.route]
        unverified = any(
            vf.verdict.status != VerdictStatus.verified for vf in verified_fields
        )
        unreadable = any(
            vf.field.status == FieldStatus.unreadable for vf in verified_fields
        )
        return unverified or unreadable


class VerifiedRecord(BaseModel):
    """System output: structured record ready for human confirmation field by field.

    NEVER auto-confirmed; always goes through human confirmation
    field by field (confirmacion-humana rule).
    Not a diagnosis or prescription: reflects what was written, verified.
    """

    prescription_id: str
    medications: list[VerifiedMedication]
    overall_confidence: float
    needs_review: bool

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def needs_review_consistent(self) -> "VerifiedRecord":
        computed = any(m.needs_review for m in self.medications)
        if computed and not self.needs_review:
            raise ValueError(
                "needs_review must be True when any medication requires review"
            )
        return self
