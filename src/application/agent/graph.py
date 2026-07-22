from typing import Any, Callable, Awaitable

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

AsyncTool = Callable[..., Awaitable[Any]]


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


def build_graph(
    vision_extract: AsyncTool,
    retrieve_drug: AsyncTool,
    verify_prescription: AsyncTool,
    detect_anomaly: AsyncTool | None = None,
    checkpointer=None,
) -> CompiledStateGraph:
    """Construye el grafo LangGraph del agente.

    El grafo pausa antes de 'human_confirm' (interrupt_before) para que el
    operador revise el VerifiedRecord campo por campo antes de aprobarlo
    (regla confirmacion-humana).
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
            return {"prescription_data": data}
        except Exception as exc:
            return {"error": str(exc)}

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

    graph.add_edge("vision_extract", "verify_prescription")
    graph.add_edge("verify_prescription", "human_confirm")
    graph.add_edge("human_confirm", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_confirm"],
    )
