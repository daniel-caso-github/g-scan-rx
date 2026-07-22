from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: ApiError | None = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(data=data, error=None)

    @classmethod
    def fail(cls, code: str, message: str) -> "ApiResponse[T]":
        return cls(data=None, error=ApiError(code=code, message=message))


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
