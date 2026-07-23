import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.agent.react_loop import ReActLoop
from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.config import settings
from src.domain.ports.guardrail import Guardrail
from src.domain.ports.image_cache import ImageCache
from src.domain.ports.tracer import Tracer
from src.infrastructure.persistence.catalog_repository import SqlAlchemyCatalogRepository
from src.interfaces.api.bootstrap import AppContainer, Bootstrap, GuardrailBootstrapError

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
        except GuardrailBootstrapError:
            # Fail-closed (GUARDRAILS_REQUIRED): abort startup, do not degrade.
            logger.error("Guardrail crítico no disponible con GUARDRAILS_REQUIRED activo; abortando arranque")
            raise
        except Exception:
            logger.exception("Error en Bootstrap; VLM no disponible")

    app.state.container = container

    yield

    if container is not None:
        container.tracer.flush()
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


def get_pii_guardrail(request: Request) -> Guardrail:
    return _container(request).pii_guardrail


def get_injection_guardrail(request: Request) -> Guardrail:
    return _container(request).injection_guardrail


def get_tracer(request: Request) -> Tracer:
    return _container(request).tracer


def get_image_cache(request: Request) -> ImageCache:
    return _container(request).image_cache
