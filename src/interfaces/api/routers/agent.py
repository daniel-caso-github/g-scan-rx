import base64
import hashlib
import logging
import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from src.application.agent.graph import AgentGraphState
from src.interfaces.api.dependencies import get_agent_graph
from src.interfaces.api.schemas import (
    AgentConfirmResponse,
    AgentStartResponse,
    AgentStateDTO,
    ApiResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


def _to_state_dto(state: AgentGraphState) -> AgentStateDTO:
    return AgentStateDTO(
        image_hash=state.get("image_hash", ""),
        prescription_data=state.get("prescription_data"),
        record_data=state.get("record_data"),
        anomaly_score=state.get("anomaly_score"),
        is_anomaly=state.get("is_anomaly", False),
        human_approved=state.get("human_approved"),
        error=state.get("error"),
    )


@router.post("/start", response_model=ApiResponse[AgentStartResponse])
async def agent_start(
    file: UploadFile = File(...),
    graph=Depends(get_agent_graph),
) -> ApiResponse[AgentStartResponse]:
    try:
        image_bytes = await file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        image_b64 = base64.b64encode(image_bytes).decode()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial: AgentGraphState = {
            "image_b64": image_b64,
            "image_hash": image_hash,
            "prescription_data": None,
            "record_data": None,
            "anomaly_score": None,
            "is_anomaly": False,
            "human_approved": None,
            "error": None,
        }

        state = await graph.ainvoke(initial, config)
        return ApiResponse.ok(
            AgentStartResponse(
                thread_id=thread_id,
                state=_to_state_dto(state),
                awaiting_confirmation=True,
            )
        )
    except Exception:
        logger.exception("Error en /agent/start")
        return ApiResponse.fail(code="AGENT_START_ERROR", message="Error interno al iniciar el agente")


@router.post("/{thread_id}/confirm", response_model=ApiResponse[AgentConfirmResponse])
async def agent_confirm(
    thread_id: str,
    graph=Depends(get_agent_graph),
) -> ApiResponse[AgentConfirmResponse]:
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await graph.ainvoke(None, config)
        if state is None:
            return ApiResponse.fail(
                code="SESSION_NOT_FOUND",
                message="Sesión no encontrada o ya finalizada",
            )
        return ApiResponse.ok(
            AgentConfirmResponse(
                thread_id=thread_id,
                state=_to_state_dto(state),
                human_approved=state.get("human_approved"),
            )
        )
    except Exception:
        logger.exception("Error en /agent/{thread_id}/confirm")
        return ApiResponse.fail(code="AGENT_CONFIRM_ERROR", message="Error interno al confirmar")
