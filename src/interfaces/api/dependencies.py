import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from google import genai
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.agent.graph import build_graph
from src.application.agent.react_loop import ReActLoop
from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.config import settings
from src.infrastructure.embedding.embedder import Embedder
from src.infrastructure.mcp.server import build_mcp_server
from src.infrastructure.normalizer.gemini_normalizer_adapter import GeminiNormalizerAdapter
from src.infrastructure.persistence.catalog_repository import SqlAlchemyCatalogRepository
from src.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from src.infrastructure.verification.catalog_verifier_adapter import CatalogVerifierAdapter
from src.infrastructure.vision.gemini_vision_adapter import GeminiVisionAdapter

logger = logging.getLogger(__name__)


def _build_gemini_use_cases():
    client = genai.Client(api_key=settings.gemini_api_key)
    extractor = GeminiVisionAdapter(
        client=client,
        model=settings.gemini_model,
        readable_threshold=settings.vision_confidence_readable,
        uncertain_threshold=settings.vision_confidence_uncertain,
    )
    normalizer = GeminiNormalizerAdapter(client=client, model=settings.gemini_model)
    extract_uc = ExtractPrescriptionUseCase(extractor=extractor, normalizer=normalizer)
    return extract_uc, normalizer


def build_extract_uc() -> ExtractPrescriptionUseCase:
    """Factory standalone para el CLI (no requiere Request ni lifespan)."""
    uc, _ = _build_gemini_use_cases()
    return uc


def _set_unavailable(app: FastAPI) -> None:
    app.state.extract_uc = None
    app.state.verify_uc = None
    app.state.react_loop = None
    app.state.agent_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    corpus = []
    try:
        async with session_factory() as session:
            repo = SqlAlchemyCatalogRepository(session)
            corpus = await repo.list_all()
        logger.info("Catálogo cargado: %d ítems", len(corpus))
    except Exception:
        logger.warning("No se pudo cargar el catálogo desde la DB; retriever arranca vacío")

    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY no configurada — endpoints de VLM no disponibles")
        _set_unavailable(app)
        yield
        await engine.dispose()
        return

    try:
        extract_uc, normalizer = _build_gemini_use_cases()
    except Exception:
        logger.exception("Error al inicializar cliente Gemini; VLM no disponible")
        _set_unavailable(app)
        yield
        await engine.dispose()
        return

    verifier = CatalogVerifierAdapter()
    embedder = Embedder()
    retriever = HybridRetriever(corpus=corpus, embedder=embedder)
    verify_uc = VerifyMedicationUseCase(
        retriever=retriever, normalizer=normalizer, verifier=verifier
    )

    mcp_server = build_mcp_server(extract_uc=extract_uc, verify_uc=verify_uc, retriever=retriever)

    async def _vision_extract(**kwargs):
        tool = await mcp_server.get_tool("vision_extract")
        return await tool.fn(**kwargs)

    async def _retrieve_drug(**kwargs):
        tool = await mcp_server.get_tool("retrieve_drug")
        return await tool.fn(**kwargs)

    async def _verify_prescription(**kwargs):
        tool = await mcp_server.get_tool("verify_prescription")
        return await tool.fn(**kwargs)

    react_loop = ReActLoop(
        vision_extract=_vision_extract,
        retrieve_drug=_retrieve_drug,
        verify_prescription=_verify_prescription,
    )
    agent_graph = build_graph(
        vision_extract=_vision_extract,
        retrieve_drug=_retrieve_drug,
        verify_prescription=_verify_prescription,
        checkpointer=MemorySaver(),
    )

    app.state.extract_uc = extract_uc
    app.state.verify_uc = verify_uc
    app.state.react_loop = react_loop
    app.state.agent_graph = agent_graph

    yield

    await engine.dispose()


def _require(attr: str, request: Request):
    value = getattr(request.app.state, attr, None)
    if value is None:
        raise HTTPException(status_code=503, detail="Servicio VLM no disponible")
    return value


def get_extract_uc(request: Request) -> ExtractPrescriptionUseCase:
    return _require("extract_uc", request)


def get_verify_uc(request: Request) -> VerifyMedicationUseCase:
    return _require("verify_uc", request)


def get_react_loop(request: Request) -> ReActLoop:
    return _require("react_loop", request)


def get_agent_graph(request: Request):
    return _require("agent_graph", request)
