from pydantic import BaseModel, field_validator


class CatalogItem(BaseModel):
    """Official drug catalog entry.

    Source of truth against which every extracted field is validated.
    Ingested idempotently from CIMA-AEMPS or DIGEMID.
    """

    id: str
    active_ingredient: str
    brand_name: str | None = None
    presentation: str
    concentration: str | None = None
    form: str | None = None
    dose_range: dict | None = None  # {"min": float, "max": float, "unit": str}
    source: str  # "cima" | "digemid"
    country: str | None = None
    embedding: list[float] | None = None

    model_config = {"frozen": True}

    @field_validator("source")
    @classmethod
    def source_valid(cls, v: str) -> str:
        if v not in {"cima", "digemid"}:
            raise ValueError("source must be 'cima' or 'digemid'")
        return v

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("id cannot be empty")
        return v
