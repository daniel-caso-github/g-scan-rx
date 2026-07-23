import base64
from unittest.mock import AsyncMock

from langgraph.checkpoint.memory import MemorySaver

from src.application.agent.graph import AgentGraphState, build_graph
from src.domain.ports.guardrail import GuardrailResult

_IMAGE_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode()
_IMAGE_HASH = "abc123"


def _prescription_dict() -> dict:
    return {
        "id": "rx-1",
        "medications": [
            {
                "drug": {"value": "amoxicilina", "status": "readable"},
                "dose": {"value": "500mg", "status": "readable"},
                "frequency": {"value": None, "status": "unreadable"},
                "duration": {"value": None, "status": "unreadable"},
                "route": {"value": None, "status": "unreadable"},
            }
        ],
    }


def _initial_state() -> AgentGraphState:
    return AgentGraphState(
        image_b64=_IMAGE_B64,
        image_hash=_IMAGE_HASH,
        prescription_data=None,
        record_data=None,
        anomaly_score=None,
        is_anomaly=False,
        human_approved=None,
        error=None,
    )


def _passing_guardrail():
    g = AsyncMock()
    g.check = AsyncMock(return_value=GuardrailResult(passed=True))
    return g


def _blocking_guardrail(risk: str):
    g = AsyncMock()
    g.check = AsyncMock(return_value=GuardrailResult(passed=False, risk_type=risk))
    return g


async def test_injection_blocks_and_skips_verify():
    vision_extract = AsyncMock(return_value=_prescription_dict())
    verify_prescription = AsyncMock(return_value={"ok": True})
    app = build_graph(
        vision_extract, AsyncMock(), verify_prescription,
        checkpointer=MemorySaver(),
        pii_guardrail=_passing_guardrail(),
        injection_guardrail=_blocking_guardrail("PROMPT_INJECTION"),
    )
    state = await app.ainvoke(_initial_state(), {"configurable": {"thread_id": "g1"}})

    assert state["error"] is not None
    assert "adversario" in state["error"]
    verify_prescription.assert_not_awaited()


async def test_pii_blocks_and_skips_verify():
    vision_extract = AsyncMock(return_value=_prescription_dict())
    verify_prescription = AsyncMock(return_value={"ok": True})
    app = build_graph(
        vision_extract, AsyncMock(), verify_prescription,
        checkpointer=MemorySaver(),
        pii_guardrail=_blocking_guardrail("PII"),
        injection_guardrail=_passing_guardrail(),
    )
    state = await app.ainvoke(_initial_state(), {"configurable": {"thread_id": "g2"}})

    assert state["error"] is not None
    assert "personales" in state["error"]
    verify_prescription.assert_not_awaited()


async def test_clean_text_passes_guardrails_and_verifies():
    vision_extract = AsyncMock(return_value=_prescription_dict())
    verify_prescription = AsyncMock(return_value={"ok": True})
    inj = _passing_guardrail()
    pii = _passing_guardrail()
    app = build_graph(
        vision_extract, AsyncMock(), verify_prescription,
        checkpointer=MemorySaver(),
        pii_guardrail=pii,
        injection_guardrail=inj,
    )
    state = await app.ainvoke(_initial_state(), {"configurable": {"thread_id": "g3"}})

    inj.check.assert_awaited_once()
    pii.check.assert_awaited_once()
    verify_prescription.assert_awaited_once()
    assert state["record_data"] == {"ok": True}
    assert state["error"] is None


async def test_no_guardrails_configured_still_verifies():
    vision_extract = AsyncMock(return_value=_prescription_dict())
    verify_prescription = AsyncMock(return_value={"ok": True})
    app = build_graph(vision_extract, AsyncMock(), verify_prescription, checkpointer=MemorySaver())
    state = await app.ainvoke(_initial_state(), {"configurable": {"thread_id": "g4"}})
    verify_prescription.assert_awaited_once()
    assert state["error"] is None
