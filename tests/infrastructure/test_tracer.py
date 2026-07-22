from src.infrastructure.observability.null_tracer import NullTracer


def test_null_tracer_trace_does_not_raise():
    tracer = NullTracer()
    tracer.trace(name="extract", input={"image_hash": "abc"}, output={"status": "ok"})


def test_null_tracer_span_is_context_manager():
    tracer = NullTracer()
    with tracer.span("extract_step") as span:
        assert span is None


def test_langfuse_tracer_falls_back_on_import_error(monkeypatch):
    """Bootstrap._build_tracer() returns NullTracer when langfuse is unavailable."""
    import sys
    import importlib

    langfuse_modules = [k for k in sys.modules if "langfuse" in k]
    saved = {k: sys.modules.pop(k) for k in langfuse_modules}

    try:
        from unittest.mock import patch

        with patch.dict("sys.modules", {"langfuse": None}):
            from src.interfaces.api.bootstrap import Bootstrap
            from src.infrastructure.observability.null_tracer import NullTracer as NT

            tracer = Bootstrap._build_tracer()
            assert isinstance(tracer, NT)
    finally:
        sys.modules.update(saved)
