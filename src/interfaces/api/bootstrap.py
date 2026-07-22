import logging
from typing import Any, Callable, Awaitable

from google import genai
from langgraph.checkpoint.memory import MemorySaver

from src.application.agent.graph import build_graph
from src.application.agent.react_loop import ReActLoop
from src.application.use_cases.extract_prescription import ExtractPrescriptionUseCase
from src.application.use_cases.verify_medication import VerifyMedicationUseCase
from src.config import settings
from src.domain.entities.catalog_item import CatalogItem
from src.domain.ports.guardrail import Guardrail
from src.domain.ports.image_cache import ImageCache
from src.domain.ports.tracer import Tracer
from src.infrastructure.cache.memory_image_cache import MemoryImageCache
from src.infrastructure.embedding.embedder import Embedder
from src.infrastructure.guardrails.null_guardrail import NullGuardrail
from src.infrastructure.mcp.server import build_mcp_server
from src.infrastructure.normalizer.gemini_normalizer_adapter import GeminiNormalizerAdapter
from src.infrastructure.observability.null_tracer import NullTracer
from src.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from src.infrastructure.verification.catalog_verifier_adapter import CatalogVerifierAdapter
from src.infrastructure.vision.gemini_vision_adapter import GeminiVisionAdapter

logger = logging.getLogger(__name__)

AsyncTool = Callable[..., Awaitable[Any]]


class AppContainer:
    """Fully wired dependency graph, ready to use."""

    def __init__(
        self,
        extract_uc: ExtractPrescriptionUseCase,
        verify_uc: VerifyMedicationUseCase,
        react_loop: ReActLoop,
        agent_graph: Any,
        pii_guardrail: Guardrail,
        injection_guardrail: Guardrail,
        tracer: Tracer,
        image_cache: ImageCache,
    ) -> None:
        self.extract_uc = extract_uc
        self.verify_uc = verify_uc
        self.react_loop = react_loop
        self.agent_graph = agent_graph
        self.pii_guardrail = pii_guardrail
        self.injection_guardrail = injection_guardrail
        self.tracer = tracer
        self.image_cache = image_cache


class Bootstrap:
    """Composition root: builds and injects all infrastructure dependencies."""

    def __init__(self, corpus: list[CatalogItem]) -> None:
        self._corpus = corpus

    def build(self) -> AppContainer:
        client = genai.Client(api_key=settings.gemini_api_key)

        tracer = self._build_tracer()

        extractor = GeminiVisionAdapter(
            client=client,
            model=settings.gemini_model,
            readable_threshold=settings.vision_confidence_readable,
            uncertain_threshold=settings.vision_confidence_uncertain,
            tracer=tracer,
        )
        normalizer = GeminiNormalizerAdapter(client=client, model=settings.gemini_model, tracer=tracer)
        verifier = CatalogVerifierAdapter()
        embedder = Embedder()
        retriever = HybridRetriever(corpus=self._corpus, embedder=embedder)

        extract_uc = ExtractPrescriptionUseCase(extractor=extractor, normalizer=normalizer)
        verify_uc = VerifyMedicationUseCase(
            retriever=retriever, normalizer=normalizer, verifier=verifier
        )

        mcp_server = build_mcp_server(
            extract_uc=extract_uc, verify_uc=verify_uc, retriever=retriever
        )

        react_loop = ReActLoop(
            vision_extract=self._make_tool(mcp_server, "vision_extract"),
            retrieve_drug=self._make_tool(mcp_server, "retrieve_drug"),
            verify_prescription=self._make_tool(mcp_server, "verify_prescription"),
        )
        agent_graph = build_graph(
            vision_extract=self._make_tool(mcp_server, "vision_extract"),
            retrieve_drug=self._make_tool(mcp_server, "retrieve_drug"),
            verify_prescription=self._make_tool(mcp_server, "verify_prescription"),
            checkpointer=MemorySaver(),
        )

        pii_guardrail = self._build_pii_guardrail()
        injection_guardrail = self._build_injection_guardrail()
        image_cache = MemoryImageCache(maxsize=settings.cache_maxsize)

        return AppContainer(
            extract_uc=extract_uc,
            verify_uc=verify_uc,
            react_loop=react_loop,
            agent_graph=agent_graph,
            pii_guardrail=pii_guardrail,
            injection_guardrail=injection_guardrail,
            tracer=tracer,
            image_cache=image_cache,
        )

    @staticmethod
    def _make_tool(mcp_server, name: str) -> AsyncTool:
        async def _tool(**kwargs):
            tool = await mcp_server.get_tool(name)
            return await tool.fn(**kwargs)
        return _tool

    @staticmethod
    def _build_pii_guardrail() -> Guardrail:
        try:
            from src.infrastructure.guardrails.pii_guardrail import PiiGuardrail
            return PiiGuardrail()
        except Exception:
            # Fail-open: log at ERROR so ops notices the degradation immediately.
            # presidio requires spacy models; missing model is a misconfiguration, not a transient error.
            logger.error("presidio no disponible — PiiGuardrail DESACTIVADO; todo texto pasará sin inspección PII")
            return NullGuardrail()

    @staticmethod
    def _build_injection_guardrail() -> Guardrail:
        try:
            from src.infrastructure.guardrails.injection_guardrail import InjectionGuardrail
            return InjectionGuardrail()
        except Exception:
            # Fail-open: log at ERROR so ops notices the degradation immediately.
            logger.error("llm-guard no disponible — InjectionGuardrail DESACTIVADO; prompt injection no será detectado")
            return NullGuardrail()

    @staticmethod
    def _build_tracer() -> Tracer:
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from src.infrastructure.observability.langfuse_tracer import LangfuseTracer
                return LangfuseTracer(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
            except Exception:
                logger.warning("Error inicializando Langfuse — trazas desactivadas")
        return NullTracer()


def build_extract_uc_standalone() -> ExtractPrescriptionUseCase:
    """Standalone factory for the CLI: builds only the extraction use case without the DB."""
    client = genai.Client(api_key=settings.gemini_api_key)
    extractor = GeminiVisionAdapter(
        client=client,
        model=settings.gemini_model,
        readable_threshold=settings.vision_confidence_readable,
        uncertain_threshold=settings.vision_confidence_uncertain,
    )
    normalizer = GeminiNormalizerAdapter(client=client, model=settings.gemini_model)
    return ExtractPrescriptionUseCase(extractor=extractor, normalizer=normalizer)
