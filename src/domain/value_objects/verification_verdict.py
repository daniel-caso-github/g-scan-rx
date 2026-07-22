from enum import StrEnum

from pydantic import BaseModel, field_validator


class VerdictStatus(StrEnum):
    verified = "verified"
    uncertain = "uncertain"
    not_found = "not_found"


class VerificationVerdict(BaseModel):
    """Result of matching a field against the official catalog.

    Failure contract: on verifier error after retry →
    status=uncertain with note "verificación no disponible". Never raises
    an exception toward the pipeline.
    """

    status: VerdictStatus
    catalog_item_id: str | None = None
    match_score: float = 0.0
    notes: list[str] = []

    model_config = {"frozen": True}

    @field_validator("match_score")
    @classmethod
    def score_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("match_score must be in [0.0, 1.0]")
        return v

    def model_post_init(self, __context: object) -> None:
        if self.status == VerdictStatus.verified and self.catalog_item_id is None:
            raise ValueError("verdict 'verified' requires catalog_item_id")

    @classmethod
    def no_disponible(cls) -> "VerificationVerdict":
        return cls(
            status=VerdictStatus.uncertain,
            notes=["verificación no disponible"],
        )
