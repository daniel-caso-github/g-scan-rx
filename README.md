# G-Scan-RX

Agentic assistant that digitizes and **verifies** handwritten medical prescriptions.

> **WARNING**: This system does NOT replace professional pharmaceutical validation. Every result requires human confirmation field by field.

---

## What it does

1. Receives a photo of a handwritten medical prescription.
2. Reads it with a VLM (Gemini 2.0 Flash) and extracts each field with its confidence level.
3. Verifies each medication against an official catalog (CIMA/DIGEMID in Postgres + pgvector).
4. **Abstains** on illegible content instead of guessing.
5. Presents a structured record for **human confirmation** field by field.

**Engineering thesis**: how do you engineer a system with LLMs when being wrong has real consequences? The goal is not to read a doctor's handwriting — it is **knowing when the system doesn't know**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  interfaces/                                                     │
│  ├── api/        FastAPI gateway — rate limiting, guardrails,   │
│  │               Prometheus metrics, Langfuse tracing            │
│  └── cli/        extract CLI (offline, for local testing)       │
├─────────────────────────────────────────────────────────────────┤
│  application/                                                    │
│  ├── use_cases/  ExtractPrescription, VerifyMedication,         │
│  │               IngestCatalog                                   │
│  └── agent/      ReActLoop (pure Python) + LangGraph graph      │
│                  with interrupt_before=["human_confirm"]         │
├─────────────────────────────────────────────────────────────────┤
│  infrastructure/                                                 │
│  ├── vision/     GeminiVisionAdapter (VLM extractor)            │
│  ├── normalizer/ GeminiNormalizerAdapter (dose → canonical)     │
│  ├── retrieval/  HybridRetriever (BM25 + pgvector + reranker)  │
│  ├── mcp/        FastMCP server with 4 agent tools              │
│  ├── guardrails/ PiiGuardrail (presidio) + InjectionGuardrail   │
│  ├── cache/      MemoryImageCache — LRU keyed by image_hash     │
│  ├── observability/ CircuitBreaker, Langfuse tracer, metrics    │
│  └── persistence/ SQLAlchemy + pgvector (catalog)               │
├─────────────────────────────────────────────────────────────────┤
│  domain/                                                         │
│  ├── entities/   Prescription, ExtractedMedication,             │
│  │               VerifiedRecord, CatalogItem                     │
│  ├── value_objects/ ExtractedField, NormalizedDose,             │
│  │               VerificationVerdict, ImageCrop                  │
│  ├── ports/      ABC: VisionExtractor, Normalizer, Retriever,   │
│  │               Verifier, AnomalyDetector, Guardrail,          │
│  │               ImageCache, Tracer                              │
│  └── services/   make_id (deterministic SHA-256)                │
└─────────────────────────────────────────────────────────────────┘
```

Dependencies always point inward. `domain/` imports nothing from other layers.

### Frontend (`frontend/`)

React + Vite SPA — the human-confirmation screen, next to the original image crop:

```
Upload → Processing → Review (field-by-field, image side-by-side) → Confirmed / Rejected
```

Every field carries its own status (legible / uncertain / abstention) and requires an explicit
accept or correction — nothing auto-confirms. Responsive from 320px up; body text meets WCAG AA
contrast (4.5:1).

---

## Requirements

- Docker + Docker Compose

---

## Configuration

Create `app.env` in the project root:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash

# Optional: Langfuse tracing
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional: threshold tuning
VISION_CONFIDENCE_READABLE=0.7
VISION_CONFIDENCE_UNCERTAIN=0.3
CACHE_MAXSIZE=256
RATE_LIMIT_EXTRACT=10/minute
RATE_LIMIT_PROCESS=10/minute
```

> `app.env` is never committed (listed in `.gitignore`).

---

## Running

```bash
# 1. Start the database
docker compose up -d app-db

# 2. Apply migrations
docker compose run --rm app alembic upgrade head

# 3. (Optional) Ingest CIMA catalog
docker compose run --rm app python -m src.interfaces.cli.ingest_catalog cima

# 4. Start the API
docker compose up -d app

# 5. Start the frontend (the human-confirmation screen)
docker compose up -d frontend

# 6. Verify
curl http://localhost:8000/health
# → {"status":"ok"}
open http://localhost:5173
```

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics (raw exposition format) |
| `GET` | `/dashboard` | Human-readable metrics dashboard (hallucination/abstention/cost/latency) |
| `POST` | `/extract` | Extract medications from an image (rate: 10/min) |
| `POST` | `/verify` | Verify a `Prescription` against the catalog |
| `POST` | `/process` | Full ReAct pipeline (rate: 10/min) |
| `POST` | `/agent/start` | Start LangGraph graph with human-in-the-loop pause |
| `POST` | `/agent/{thread_id}/confirm` | Resume graph after human confirmation |

### Example: `/extract`

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@synthetic_prescription.jpg"
```

Response:
```json
{
  "data": {
    "id": "a3f9...",
    "status": "pending",
    "medications": [
      {
        "drug":      {"value": "amoxicillin", "confidence": 0.92, "status": "readable"},
        "dose":      {"value": "500mg",       "confidence": 0.85, "status": "readable"},
        "frequency": {"value": "every 8h",   "confidence": 0.78, "status": "readable"},
        "duration":  {"value": null,          "confidence": 0.1,  "status": "unreadable"},
        "route":     {"value": "oral",        "confidence": 0.95, "status": "readable"}
      }
    ]
  },
  "error": null
}
```

Fields with `status: "unreadable"` indicate abstention — the system does not guess.

---

## Tests

```bash
docker compose run --rm app pytest -v
```

Tests are **offline-first**: synthetic fixtures, mocked VLM/LLM/HTTP calls. No real network.

```bash
# Single module
docker compose run --rm app pytest -v -k "test_react_loop"

# Lint
docker compose run --rm app ruff check src tests
```

---

## Metrics dashboard

`GET /dashboard` renders a self-contained HTML page with the four metrics the project's engineering
thesis cares about most — **hallucination, abstention, cost, and latency** — computed live from the
in-process Prometheus counters below:

```bash
docker compose up -d app
open http://localhost:8000/dashboard   # or just curl it
```

- **Hallucination rate**: share of drug verdicts that came back `not_found` against the catalog — a
  drug the VLM extracted that doesn't match anything real.
- **Abstention rate**: share of `/process` attempts where the agent abstained on an out-of-distribution image.
- **Cost / tokens**: cumulative Gemini spend and token usage.
- **Average latency**: mean HTTP request duration across all endpoints.

All figures are cumulative **since the API process started** — there's no Prometheus/Grafana server
in this stack (deliberately; see the ADR on not deploying a public demo), so there's no time series
or real percentiles, only an in-process average. Restarting the API resets the counters.

## Prometheus Metrics

| Metric | Description |
|---|---|
| `gscan_requests_total` | HTTP requests by endpoint and status code |
| `gscan_request_duration_seconds` | Latency by endpoint |
| `gscan_extractions_total` | Extractions by result (success, cache_hit, error, pii_blocked, injection_blocked) |
| `gscan_verdicts_total` | Drug verification verdicts by status (`not_found` is the hallucination proxy) |
| `gscan_abstentions_total` | Agent abstentions (OOD image) |
| `gscan_tokens_total` | Gemini tokens consumed by model and direction |
| `gscan_cost_usd_total` | Estimated cost in USD by model |
| `gscan_cache_hits_total` | Cache hits (extraction avoided) |
| `gscan_circuit_open_total` | Requests rejected by open circuit breaker |

---

## Security

- **Zero real data**: no real patient prescriptions ever enter the system. Everything is synthetic/fictional.
- **PII guardrail**: `presidio-analyzer` detects identifiable data in extracted text; if detected, the response is blocked entirely.
- **Prompt injection**: `llm-guard` inspects extracted text before passing it to downstream models.
- **Circuit breakers**: Gemini adapters have a circuit breaker (5 failures → OPEN for 60s) to degrade gracefully.
- **Rate limiting**: `/extract` and `/process` are limited to 10 requests/minute per IP.

---

## License

MIT — see [LICENSE](LICENSE).
