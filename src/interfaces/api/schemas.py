from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse[T](BaseModel):
    data: T | None = None
    error: ApiError | None = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(data=data, error=None)

    @classmethod
    def fail(cls, code: str, message: str) -> "ApiResponse[T]":
        return cls(data=None, error=ApiError(code=code, message=message))


class GuardrailsHealth(BaseModel):
    pii: str
    injection: str


class HealthResponse(BaseModel):
    status: str
    guardrails: GuardrailsHealth | None = None


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
