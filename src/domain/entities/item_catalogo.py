from pydantic import BaseModel, field_validator


class ItemCatalogo(BaseModel):
    """Entrada del catálogo oficial de medicamentos.

    Fuente de verdad contra la que se valida todo campo extraído.
    Ingestada idempotentemente desde CIMA-AEMPS o DIGEMID.
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
    def source_valida(cls, v: str) -> str:
        if v not in {"cima", "digemid"}:
            raise ValueError("source debe ser 'cima' o 'digemid'")
        return v

    @field_validator("id")
    @classmethod
    def id_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("id no puede estar vacío")
        return v
