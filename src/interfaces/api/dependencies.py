import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.application.agent.react_loop import ReActLoop
from src.config import settings
from src.interfaces.api.bootstrap import AppContainer, Bootstrap
from src.infrastructure.persistence.catalog_repository import SqlAlchemyCatalogRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    corpus = []
    try:
        async with session_factory() as session:
            corpus = await SqlAlchemyCatalogRepository(session).list_all()
        logger.info("Catálogo cargado: %d ítems", len(corpus))
    except Exception:
        logger.warning("No se pudo cargar el catálogo desde la DB; retriever arranca vacío")

    container: AppContainer | None = None
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY no configurada — endpoints de VLM no disponibles")
    else:
        try:
            container = Bootstrap(corpus).build()
        except Exception:
            logger.exception("Error en Bootstrap; VLM no disponible")

    app.state.container = container

    yield

    await engine.dispose()


def _container(request: Request) -> AppContainer:
    container: AppContainer | None = request.app.state.container
    if container is None:
        raise HTTPException(status_code=503, detail="Servicio VLM no disponible")
    return container


def get_extract_uc(request: Request) -> ExtractPrescriptionUseCase:
    return _container(request).extract_uc


def get_verify_uc(request: Request) -> VerifyMedicationUseCase:
    return _container(request).verify_uc


def get_react_loop(request: Request) -> ReActLoop:
    return _container(request).react_loop


def get_agent_graph(request: Request):
    return _container(request).agent_graph
