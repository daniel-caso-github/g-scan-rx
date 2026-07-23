import base64
from unittest.mock import AsyncMock

from langgraph.checkpoint.memory import MemorySaver

from src.application.agent.graph import AgentGraphState, build_graph
from src.domain.entities.catalog_item import CatalogItem
from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict

_CROP = ImageCrop(bbox=(0, 0, 100, 30), crop_ref="test")
_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n"
_IMAGE_B64 = base64.b64encode(_IMAGE_BYTES).decode()
_IMAGE_HASH = "abc123"


def _field(value="amoxicilina") -> ExtractedField:
    return ExtractedField(value=value, confidence=0.95, status=FieldStatus.readable, source_crop=_CROP)


def _prescription_dict() -> dict:
    med = ExtractedMedication(
        drug=_field("amoxicilina"), dose=_field("500mg"),
        frequency=_field("cada 8h"), duration=_field("7 días"),
        route=_field("oral"), crop=_CROP,
    )
    return Prescription(
        id="rx-001", image_hash=_IMAGE_HASH,
        medications=[med], status=PrescriptionStatus.pending,
    ).model_dump()


def _verified_record_dict(needs_review: bool = False) -> dict:
    vf = VerifiedField(
        field=_field(),
        verdict=VerificationVerdict(
            status=VerdictStatus.verified, catalog_item_id="cat-1", match_score=1.0,
        ),
    )
    med = VerifiedMedication(
        drug=vf, dose=vf, frequency=vf, duration=vf, route=vf,
        catalog_match=CatalogItem(
            id="cat-1", active_ingredient="amoxicilina",
            presentation="capsulas", source="cima",
        ),
    )
    return VerifiedRecord(
        prescription_id="rx-001", medications=[med],
        overall_confidence=0.95, needs_review=needs_review,
    ).model_dump()


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


def _make_tools(anomaly_score=None):
    vision_extract = AsyncMock(return_value=_prescription_dict())
    retrieve_drug = AsyncMock(return_value=[])
    verify_prescription = AsyncMock(return_value=_verified_record_dict())
    detect_anomaly = None
    if anomaly_score is not None:
        detect_anomaly = AsyncMock(
            return_value={"score": anomaly_score, "is_anomaly": anomaly_score > 0.5}
        )
    return vision_extract, retrieve_drug, verify_prescription, detect_anomaly


async def test_graph_pauses_before_human_confirm():
    vision_extract, retrieve_drug, verify_prescription, _ = _make_tools()
    app = build_graph(vision_extract, retrieve_drug, verify_prescription, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "t1"}}

    state = await app.ainvoke(_initial_state(), config)

    assert state["prescription_data"] is not None
    assert state["record_data"] is not None
    assert state["human_approved"] is None


async def test_graph_resumes_after_human_confirm():
    vision_extract, retrieve_drug, verify_prescription, _ = _make_tools()
    app = build_graph(vision_extract, retrieve_drug, verify_prescription, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "t2"}}

    await app.ainvoke(_initial_state(), config)
    final_state = await app.ainvoke(None, config)

    assert final_state["human_approved"] is True


async def test_graph_without_anomaly_detector_calls_extract_and_verify():
    vision_extract, retrieve_drug, verify_prescription, _ = _make_tools()
    app = build_graph(vision_extract, retrieve_drug, verify_prescription, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "t3"}}

    await app.ainvoke(_initial_state(), config)

    vision_extract.assert_awaited_once()
    verify_prescription.assert_awaited_once()


async def test_graph_with_anomaly_detector_no_anomaly_runs_full_flow():
    vision_extract, retrieve_drug, verify_prescription, detect_anomaly = _make_tools(anomaly_score=0.1)
    app = build_graph(
        vision_extract, retrieve_drug, verify_prescription,
        detect_anomaly=detect_anomaly, checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "t4"}}

    state = await app.ainvoke(_initial_state(), config)

    detect_anomaly.assert_awaited_once()
    vision_extract.assert_awaited_once()
    assert state["is_anomaly"] is False
    assert state["record_data"] is not None


async def test_graph_anomaly_detected_stops_before_extract():
    vision_extract, retrieve_drug, verify_prescription, detect_anomaly = _make_tools(anomaly_score=0.9)
    app = build_graph(
        vision_extract, retrieve_drug, verify_prescription,
        detect_anomaly=detect_anomaly, checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "t5"}}

    state = await app.ainvoke(_initial_state(), config)

    assert state["is_anomaly"] is True
    vision_extract.assert_not_awaited()
    verify_prescription.assert_not_awaited()


async def test_graph_verify_prescription_receives_prescription_data():
    vision_extract, retrieve_drug, verify_prescription, _ = _make_tools()
    app = build_graph(vision_extract, retrieve_drug, verify_prescription, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "t6"}}

    await app.ainvoke(_initial_state(), config)

    call_kwargs = verify_prescription.call_args.kwargs
    assert call_kwargs["prescription_data"]["id"] == "rx-001"


async def test_graph_error_in_extract_propagates_to_state():
    vision_extract = AsyncMock(side_effect=RuntimeError("fallo VLM"))
    retrieve_drug = AsyncMock(return_value=[])
    verify_prescription = AsyncMock(return_value=_verified_record_dict())
    app = build_graph(vision_extract, retrieve_drug, verify_prescription, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "t7"}}

    state = await app.ainvoke(_initial_state(), config)

    assert state["error"] is not None
    assert "fallo VLM" in state["error"]
