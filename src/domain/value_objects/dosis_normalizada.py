from pydantic import BaseModel, field_validator

UNIDADES_CANONICAS = {
    "mg", "mcg", "g", "ml", "l", "ui", "meq",
    "comprimido", "capsula", "ampolla", "sobre", "supositorio", "parche",
    "gota", "puff", "aplicacion",
}

VIAS_CANONICAS = {
    "oral", "iv", "im", "sc", "topica", "inhalatoria",
    "rectal", "sublingual", "transdermica", "oftalmica", "otica", "nasal",
}


class DosisNormalizada(BaseModel):
    """Dosis/frecuencia/duración en unidades canónicas.

    Si no se puede normalizar con confianza, el campo se marca dudoso en
    CampoExtraido — nunca se inventa un valor canónico.
    """

    amount: float
    unit: str
    frequency_hours: float | None = None
    duration_days: float | None = None
    route: str | None = None

    model_config = {"frozen": True}

    @field_validator("amount")
    @classmethod
    def amount_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount debe ser positivo")
        return v

    @field_validator("unit")
    @classmethod
    def unit_canonica(cls, v: str) -> str:
        normalizada = v.lower().strip()
        if normalizada not in UNIDADES_CANONICAS:
            raise ValueError(f"unidad '{v}' no reconocida; usar una de {UNIDADES_CANONICAS}")
        return normalizada

    @field_validator("route")
    @classmethod
    def route_canonica(cls, v: str | None) -> str | None:
        if v is None:
            return None
        normalizada = v.lower().strip()
        if normalizada not in VIAS_CANONICAS:
            raise ValueError(f"vía '{v}' no reconocida; usar una de {VIAS_CANONICAS}")
        return normalizada
