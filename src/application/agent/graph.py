import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from src.domain.ports.guardrail import Guardrail

logger = logging.getLogger(__name__)

AsyncTool = Callable[..., Awaitable[Any]]

_FIELD_NAMES = ("drug", "dose", "frequency", "duration", "route")


def _extracted_text(prescription_data: dict | None) -> str:
    """Concatenate readable field values from a serialized Prescription."""
    if not prescription_data:
        return ""
    parts: list[str] = []
    for med in prescription_data.get("medications", []):
        for name in _FIELD_NAMES:
            field = med.get(name) or {}
            value = field.get("value")
            if value:
                parts.append(str(value))
    return " ".join(parts)


class AgentGraphState(TypedDict):
    image_b64: str
    image_hash: str
    prescription_data: dict | None
    record_data: dict | None
    anomaly_score: float | None
    is_anomaly: bool
    human_approved: bool | None
    error: str | None


def _route_after_detect(state: AgentGraphState) -> str:
    return "vision_extract" if not state.get("is_anomaly") else END


def _route_after_extract(state: AgentGraphState) -> str:
    """Skip verification if extraction failed or a guardrail blocked the text."""
    return END if state.get("error") else "verify_prescription"


def build_graph(
    vision_extract: AsyncTool,
    retrieve_drug: AsyncTool,
    verify_prescription: AsyncTool,
    detect_anomaly: AsyncTool | None = None,
    checkpointer=None,
    pii_guardrail: Guardrail | None = None,
    injection_guardrail: Guardrail | None = None,
) -> CompiledStateGraph:
    """Construye el grafo LangGraph del agente.

    El grafo pausa antes de 'human_confirm' (interrupt_before) para que el
    operador revise el VerifiedRecord campo por campo antes de aprobarlo
    (regla confirmacion-humana).

    Tras la extracción por el VLM se aplican los guardrails (inyección + PII)
    sobre el texto extraído — mismo comportamiento que el endpoint /extract —
    para no filtrar contenido adversario ni PII al resto del pipeline.
    """
    graph = StateGraph(AgentGraphState)

    async def node_detect_anomaly(state: AgentGraphState) -> dict:
        result = await detect_anomaly(image_b64=state["image_b64"])
        return {
            "anomaly_score": result["score"],
            "is_anomaly": result["is_anomaly"],
        }

    async def node_vision_extract(state: AgentGraphState) -> dict:
        try:
            data = await vision_extract(
                image_b64=state["image_b64"],
                image_hash=state["image_hash"],
            )
        except Exception as exc:
            return {"error": str(exc)}

        guard_error = await _apply_guardrails(data, state.get("image_hash", ""))
        if guard_error is not None:
            return {"prescription_data": data, "error": guard_error}
        return {"prescription_data": data}

    async def _apply_guardrails(data: dict | None, image_hash: str) -> str | None:
        text = _extracted_text(data)
        if not text:
            return None
        if injection_guardrail is not None:
            result = await injection_guardrail.check(text)
            if not result.passed:
                logger.warning("Inyección detectada en /agent; image_hash=%s", image_hash)
                return "Contenido adversario detectado en la imagen"
        if pii_guardrail is not None:
            result = await pii_guardrail.check(text)
            if not result.passed:
                logger.error("PII detectado en /agent; image_hash=%s", image_hash)
                return "La imagen contiene datos personales identificables; no se puede procesar"
        return None

    async def node_verify_prescription(state: AgentGraphState) -> dict:
        try:
            data = await verify_prescription(prescription_data=state["prescription_data"])
            return {"record_data": data}
        except Exception as exc:
            return {"error": str(exc)}

    def node_human_confirm(state: AgentGraphState) -> dict:
        return {"human_approved": True}

    if detect_anomaly is not None:
        graph.add_node("detect_anomaly", node_detect_anomaly)
        graph.add_edge(START, "detect_anomaly")
        graph.add_conditional_edges(
            "detect_anomaly",
            _route_after_detect,
            {"vision_extract": "vision_extract", END: END},
        )
    else:
        graph.add_edge(START, "vision_extract")

    graph.add_node("vision_extract", node_vision_extract)
    graph.add_node("verify_prescription", node_verify_prescription)
    graph.add_node("human_confirm", node_human_confirm)

    graph.add_conditional_edges(
        "vision_extract",
        _route_after_extract,
        {"verify_prescription": "verify_prescription", END: END},
    )
    graph.add_edge("verify_prescription", "human_confirm")
    graph.add_edge("human_confirm", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_confirm"],
    )
