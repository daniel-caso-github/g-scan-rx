import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.catalog_item import CatalogItem
from src.domain.entities.extracted_medication import ExtractedMedication
from src.domain.entities.prescription import Prescription, PrescriptionStatus
from src.domain.entities.verified_record import VerifiedField, VerifiedMedication, VerifiedRecord
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus
from src.domain.value_objects.image_crop import ImageCrop
from src.domain.value_objects.verification_verdict import VerdictStatus, VerificationVerdict
from src.infrastructure.mcp.server import build_mcp_server

_CROP = ImageCrop(bbox=(0, 0, 100, 30), crop_ref="test")
_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n"
_IMAGE_B64 = base64.b64encode(_IMAGE_BYTES).decode()
_IMAGE_HASH = "abc123"


def _field(value="amoxicilina") -> ExtractedField:
    return ExtractedField(value=value, confidence=0.95, status=FieldStatus.readable, source_crop=_CROP)


def _medication() -> ExtractedMedication:
    return ExtractedMedication(
        drug=_field("amoxicilina"),
        dose=_field("500mg"),
        frequency=_field("cada 8h"),
        duration=_field("7 días"),
        route=_field("oral"),
        crop=_CROP,
    )


def _prescription() -> Prescription:
    return Prescription(
        id="rx-001",
        image_hash=_IMAGE_HASH,
        medications=[_medication()],
        status=PrescriptionStatus.pending,
    )


def _catalog_item() -> CatalogItem:
    return CatalogItem(
        id="cat-1",
        active_ingredient="amoxicilina",
        presentation="capsulas",
        source="cima",
    )


def _verdict(status=VerdictStatus.verified) -> VerificationVerdict:
    return VerificationVerdict(status=status, catalog_item_id="cat-1", match_score=1.0)


def _verified_record() -> VerifiedRecord:
    vf = VerifiedField(field=_field(), verdict=_verdict())
    med = VerifiedMedication(
        drug=vf,
        dose=vf,
        frequency=vf,
        duration=vf,
        route=vf,
        catalog_match=_catalog_item(),
    )
    return VerifiedRecord(
        prescription_id="rx-001",
        medications=[med],
        overall_confidence=0.95,
        needs_review=False,
    )


def _make_mocks(prescription=None, verified_record=None, retrieval_result=None):
    extract_uc = MagicMock()
    extract_uc.execute = AsyncMock(return_value=prescription or _prescription())

    verify_uc = MagicMock()
    verify_uc.execute = AsyncMock(return_value=verified_record or _verified_record())

    retriever = MagicMock()
    retriever.retrieve = AsyncMock(
        return_value=retrieval_result if retrieval_result is not None else [(_catalog_item(), 0.9)]
    )

    return extract_uc, verify_uc, retriever


async def test_vision_extract_returns_prescription_dict():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("vision_extract")
    result = await tool.fn(image_b64=_IMAGE_B64, image_hash=_IMAGE_HASH)
    assert result["id"] == "rx-001"
    assert result["image_hash"] == _IMAGE_HASH
    assert len(result["medications"]) == 1


async def test_vision_extract_decodes_base64_correctly():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("vision_extract")
    await tool.fn(image_b64=_IMAGE_B64, image_hash=_IMAGE_HASH)
    extract_uc.execute.assert_awaited_once_with(_IMAGE_BYTES, _IMAGE_HASH)


async def test_retrieve_drug_returns_list_of_dicts():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("retrieve_drug")
    result = await tool.fn(query="amoxicilina", top_k=3)
    assert len(result) == 1
    assert result[0]["score"] == pytest.approx(0.9)
    assert result[0]["item"]["active_ingredient"] == "amoxicilina"


async def test_retrieve_drug_forwards_top_k():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("retrieve_drug")
    await tool.fn(query="paracetamol", top_k=3)
    retriever.retrieve.assert_awaited_once_with("paracetamol", top_k=3)


async def test_retrieve_drug_empty_results():
    extract_uc, verify_uc, retriever = _make_mocks(retrieval_result=[])
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("retrieve_drug")
    result = await tool.fn(query="fármaco-desconocido", top_k=5)
    assert result == []


async def test_verify_prescription_returns_verified_record():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("verify_prescription")
    prescription_data = _prescription().model_dump()
    result = await tool.fn(prescription_data=prescription_data)
    assert result["prescription_id"] == "rx-001"
    assert result["needs_review"] is False
    assert len(result["medications"]) == 1


async def test_verify_prescription_validates_prescription_model():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("verify_prescription")
    with pytest.raises(Exception):
        await tool.fn(prescription_data={"invalid": "data"})


async def test_detect_anomaly_not_registered_without_detector():
    extract_uc, verify_uc, retriever = _make_mocks()
    server = build_mcp_server(extract_uc, verify_uc, retriever)
    tool = await server.get_tool("detect_anomaly")
    assert tool is None


async def test_detect_anomaly_registered_with_detector():
    extract_uc, verify_uc, retriever = _make_mocks()
    anomaly_detector = MagicMock()
    anomaly_detector.score = AsyncMock(return_value=0.2)
    server = build_mcp_server(extract_uc, verify_uc, retriever, anomaly_detector=anomaly_detector)
    tool = await server.get_tool("detect_anomaly")
    assert tool is not None
    result = await tool.fn(image_b64=_IMAGE_B64)
    assert result["score"] == pytest.approx(0.2)
    assert result["is_anomaly"] is False


async def test_detect_anomaly_is_anomaly_true_when_score_above_threshold():
    extract_uc, verify_uc, retriever = _make_mocks()
    anomaly_detector = MagicMock()
    anomaly_detector.score = AsyncMock(return_value=0.8)
    server = build_mcp_server(extract_uc, verify_uc, retriever, anomaly_detector=anomaly_detector)
    tool = await server.get_tool("detect_anomaly")
    result = await tool.fn(image_b64=_IMAGE_B64)
    assert result["is_anomaly"] is True
