from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class AgentStateDTO(BaseModel):
    image_hash: str
    prescription_data: dict | None
    record_data: dict | None
    anomaly_score: float | None
    is_anomaly: bool
    human_approved: bool | None
    error: str | None


class AgentStartResponse(BaseModel):
    thread_id: str
    state: AgentStateDTO
    awaiting_confirmation: bool


class AgentConfirmResponse(BaseModel):
    thread_id: str
    state: AgentStateDTO
    human_approved: bool | None
