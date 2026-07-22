FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

FROM base AS deps
COPY pyproject.toml ./
RUN uv sync --no-dev --extra catalog --extra vision --extra retrieval \
    --extra agent --extra guardrails --extra observability --extra api

FROM base AS final
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY src/ ./src/
COPY scripts/ ./scripts/

CMD ["uvicorn", "src.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
