from pydantic import BaseModel, field_validator

CANONICAL_UNITS = {
    "mg", "mcg", "g", "ml", "l", "ui", "meq",
    "comprimido", "capsula", "ampolla", "sobre", "supositorio", "parche",
    "gota", "puff", "aplicacion",
}

CANONICAL_ROUTES = {
    "oral", "iv", "im", "sc", "topica", "inhalatoria",
    "rectal", "sublingual", "transdermica", "oftalmica", "otica", "nasal",
}


class NormalizedDose(BaseModel):
    """Dose/frequency/duration in canonical units.

    If normalization cannot be done with confidence, the field is marked
    uncertain in ExtractedField — a canonical value is never invented.
    """

    amount: float
    unit: str
    frequency_hours: float | None = None
    duration_days: float | None = None
    route: str | None = None

    model_config = {"frozen": True}

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("unit")
    @classmethod
    def unit_canonical(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in CANONICAL_UNITS:
            raise ValueError(f"unit '{v}' not recognized; use one of {CANONICAL_UNITS}")
        return normalized

    @field_validator("route")
    @classmethod
    def route_canonical(cls, v: str | None) -> str | None:
        if v is None:
            return None
        normalized = v.lower().strip()
        if normalized not in CANONICAL_ROUTES:
            raise ValueError(f"route '{v}' not recognized; use one of {CANONICAL_ROUTES}")
        return normalized
