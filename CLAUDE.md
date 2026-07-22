# CLAUDE.md

Este archivo guía a Claude Code (claude.ai/code) al trabajar en este repositorio.

## Proyecto

**G-Scan-RX** — asistente agéntico que digitaliza y **verifica** recetas médicas manuscritas. Toma
la foto de una receta, la lee con un VLM, **verifica cada campo contra un catálogo oficial de
medicamentos**, **se abstiene** ante lo ilegible en vez de adivinar, y presenta una ficha
estructurada para **confirmación humana** campo por campo junto al recorte de la imagen original.

Tesis de ingeniería: *¿cómo se ingenieriza un sistema con LLMs cuando equivocarse tiene
consecuencias reales?* El eje no es leer letra de médico — es **saber cuándo el sistema no sabe**.

> ⚠️ **Estado actual: Fases 1 y 2 implementadas.** Domain, eval harness, catálogo (CIMA + pgvector),
> retrieval híbrido y 61 tests passing. Antes de continuar, entrar por la wiki
> (`wiki/phases/phases-index.md`) y respetar las reglas `approved`.

## Arquitectura de código: Clean Architecture

Cuatro capas estrictas. **La dirección de las dependencias va siempre hacia adentro** (interfaces →
infrastructure → application → domain). Domain no importa de nadie. (Heredado del proyecto Job Match.)

```
src/
├── domain/                        # pura — sin frameworks externos (excepto Pydantic)
│   ├── entities/                  # Prescription, ExtractedMedication, VerifiedRecord, CatalogItem
│   ├── value_objects/             # ExtractedField, NormalizedDose, VerificationVerdict, ImageCrop
│   ├── services/                  # make_id, dose normalization (pure functions)
│   └── ports/                     # ABC: VisionExtractor, Normalizer, CatalogRepository, Retriever,
│                                  #   Verifier, AnomalyDetector
├── application/
│   ├── use_cases/                 # IngestCatalog, ExtractPrescription, VerifyMedication, ScorePrescription
│   └── agent/                     # ReAct loop → LangGraph (agentic core)
├── infrastructure/                # implementa los ports del domain
│   ├── config.py                  # Settings (reads env)
│   ├── vision/                    # cloud VLM (document vision)
│   ├── normalizer/                # local MLX normalizer (text → canonical JSON)
│   ├── catalog/                   # CIMA / DIGEMID → CatalogItem
│   ├── retrieval/                 # hybrid BM25 + vector + reranker
│   ├── embedding/                 # sentence-transformers (BGE-M3 / e5)
│   ├── mcp/                       # agent tools via MCP (fastmcp)
│   ├── guardrails/                # presidio (PII) + llm-guard (injection) + OOD
│   ├── observability/             # langfuse + prometheus + otel
│   └── persistence/               # SQLAlchemy: catalog in Postgres + pgvector
└── interfaces/                    # entrypoints
    ├── api/                       # FastAPI: gateway + verification endpoints
    └── cli/                       # ingest-catalog, extract, eval, finetune (entrypoints)
```

Además de estas 4 capas de **código**, la spec describe 4 capas **funcionales de runtime**
(gateway → núcleo agéntico → cinturón de herramientas → capa de modelos). Son ejes distintos; ver
`wiki/concepts/clean-architecture.md` y `wiki/concepts/pipeline.md`.

**Reglas de oro:**
- `domain/` **NO** importa de `infrastructure/`, `application/`, `interfaces/`, ni librerías pesadas
  (excepto Pydantic).
- `application/use_cases/*` y el agente reciben **ports** por constructor (DIP). No conocen
  implementaciones concretas.
- Persistencia del catálogo vía `select()` / `pg_insert()` sobre `orm_models`. **Cero SQL en duro.**
  Schema por Alembic.
- Un único lugar (`interfaces/api/dependencies.py`) cablea ports → implementaciones concretas.

## Workflow: Docker para servicios, MLX en el host

- **Servicios** (Postgres+pgvector, API/gateway, reranker/embeddings) corren en **Docker**. `uv` vive
  en la imagen; no hay `.venv` local para el servicio.
- **Fine-tuning e inferencia MLX** corren en el **host Apple Silicon** (Mac Mini M3 Pro, 18 GB) —
  MLX no va en Docker. Antes de entrenar: `sudo sysctl iogpu.wired_limit_mb=14336`.
- **No entrenar con todo levantado**: Postgres + reranker + embeddings consumen 4-6 GB. Entrenar en
  aislamiento; desarrollar con el modelo ya afinado y cuantizado.

```bash
docker compose build                                                   # tras cambios en deps/Dockerfile
docker compose up -d app-db                                            # Postgres+pgvector
docker compose up -d api                                               # FastAPI / gateway
docker compose run --rm app pytest -v                                  # tests (offline-first)
docker compose run --rm app ruff check src tests                       # lint
docker compose run --rm app alembic upgrade head                       # migraciones del catálogo
# MLX en el host (no Docker):
python -m mlx_lm.lora --model <base> --train --data data/norm ...      # fine-tuning (Fase 4)
mlx_lm.server --model <afinado>                                        # servir normalizador (API OpenAI)
```

Hay skills atajo proyecto-locales — ver **Skills** más abajo.

## Skills (`.claude/skills/`)

Skills invocables como `/<nombre>`. Preferí usarlas antes de tipear comandos a mano: encapsulan el
flujo correcto y las reglas del proyecto.

| Skill | Cuándo usarla | Qué hace |
|---|---|---|
| `/test [-k patrón]` | tests, iterar TDD | `pytest -v` en Docker, con filtro opcional. Reporta sin auto-fix |
| `/check` | gate pre-commit | pytest + ruff combinados; primer fallo de cada uno |
| `/build` | tras cambiar deps/Dockerfile | `docker compose build app` |
| `/review` | antes de commit / cerrar feature | code review del diff contra las convenciones. Solo reporta |
| `/migrate` | tras editar `orm_models.py` | autogenera revision Alembic (verifica pgvector/HNSW), aplica |
| `/db-shell` | inspección ad-hoc del catálogo | `psql` contra `app-db`. Solo lectura/exploración |
| `/ingest-catalog <cima\|digemid> [--limit N] [--dry-run]` | cargar el catálogo | corre `IngestCatalogUseCase`; upsert idempotente a pgvector |
| `/extract <img> [--print]` | correr el pipeline de visión sobre una receta | VLM → normalización → confianza por campo. Datos sintéticos/ficticios únicamente |
| `/eval [--suite golden]` | medir contra el golden set | corre el harness (métricas por campo + LLM-as-judge). **Se construye/usa antes del fine-tuning** |
| `/finetune <exp-a\|exp-b> [--model base]` | afinar el normalizador (host MLX) | LoRA con `mlx-lm` (o `mlx-vlm` en exp-b). No en Docker |
| `/add-tool <name>` | añadir una herramienta al agente | scaffold de una tool MCP (contrato + registro + tests). No toca tools existentes |
| `/ingest <regla o lógica>` | asentar lógica/decisión en la LLM Wiki | crea la nota en `wiki/` (reglas nacen `draft`), enlaza, log, `/lint`. **No programa nada** |
| `/lint` | tras `/ingest` o editar el vault | links rotos, huérfanas, frontmatter, coherencia spec↔código. Solo reporta |

### Agents (`.claude/agents/`)

Subagents proyecto-locales (invocables por nombre vía Task tool o como teammates de un Agent Team).
Los *reviewers* solo reportan; los *implementers* editan código y corren tests.

| Agent | Rol | Escribe |
|---|---|---|
| `code-reviewer` | review general del diff (bugs, seguridad, perf, mantenibilidad) | no |
| `clean-arch-reviewer` | valida la Clean Architecture (dependencias, ports, sin SQL en duro) | no |
| `verify-rule-reviewer` | audita coherencia reglas `approved` ↔ código (`implements_in`) | no |
| `rule-implementer` | baja a código una regla **`approved`** + actualiza `implements_in` + tests | sí |
| `new-test-implementer` | escribe tests offline-first (fixtures + mocks) y corre la suite | sí |
| `tool-adder` | agrega una herramienta MCP al agente (contrato + tests + nota wiki) | sí |
| `migration-reviewer` | revisa migraciones Alembic (pgvector, HNSW, diff vs ORM) | no |
| `eval-reviewer` | audita el harness de eval y las métricas alucinación/abstención por campo | no |
| `security-auditor` | audita PII/health data, prompt injection, guardrails, OWASP LLM | no |
| `wiki-ingester` | ejecuta el protocolo `ingest` en el vault (solo wiki, nunca código) | wiki |
| `wiki-curator` | cura el vault: links rotos, huérfanas, frontmatter, `index` | wiki |
| `wiki-diagrammer` | crea/actualiza diagramas Mermaid (ER, pipeline, ciclos) | wiki |
| `wiki-synthesizer` | consolida análisis/hallazgos en una nota `draft` estructurada | wiki |
| `adr-writer` | escribe ADRs en `wiki/decisions/` | wiki |
| `glossary-maintainer` | mantiene el glosario del dominio en la wiki | wiki |

Los agents `wiki-*`, `adr-writer` y `glossary-maintainer` **solo escriben dentro del vault**, nunca en
el código. Las reglas que crean nacen `draft`. Los `rule-implementer` no tocan reglas `draft`
(esperan promoción a `approved`). Los agents leen la LLM Wiki vía `permissions.additionalDirectories`.

#### Routing — qué agent usar según la tarea

| Si la tarea es… | Usá |
|---|---|
| entender/analizar el schema del catálogo o una migración | `migration-reviewer` |
| validar la Clean Architecture (capas, ports, dependencias) | `clean-arch-reviewer` |
| revisar un diff antes de commit | `code-reviewer` (+ `clean-arch-reviewer` si tocó capas) |
| auditar que el código cumple una regla `approved` | `verify-rule-reviewer` |
| **implementar** una regla `approved` en código | `rule-implementer` |
| escribir/ampliar tests | `new-test-implementer` |
| agregar una herramienta MCP al agente | `tool-adder` |
| revisar el harness de eval / métricas de abstención | `eval-reviewer` |
| seguridad: PII, health data, inyección, guardrails | `security-auditor` |
| crear/estructurar notas en la LLM Wiki (`ingest`) | `wiki-ingester` |

## Convenciones de código

- **Pydantic v2** para entidades de dominio y value objects. No dataclasses ni dicts crudos cuando
  hay schema. Excepción: `Settings` en `infrastructure/config.py`.
- **Seguridad primero**: ante cualquier duda de lectura, **abstenerse** (ver
  `wiki/rules/abstencion-obligatoria.md`). Nunca inventar un valor plausible.
- **Validación externa obligatoria**: todo campo se contrasta contra el catálogo antes de la ficha
  (`wiki/rules/validacion-catalogo-obligatoria.md`).
- **Cero datos reales**: nunca recetas reales de pacientes; todo sintético/ficticio
  (`wiki/rules/cero-datos-reales.md`).
- **Idempotencia**: IDs vía `make_id`; ingesta del catálogo vía `pg_insert.on_conflict_do_update`.
- **Retries `tenacity`** en todo cliente HTTP/LLM/VLM externo (429, 5xx, timeouts).
- **Contrato de fallo**: los adaptadores de modelo **nunca levantan** hacia el pipeline; degradan a
  `uncertain`/abstención para que la ficha caiga a confirmación humana en vez de romper.
- **Tests offline-first**: fixtures sintéticas en `tests/fixtures/`, mocks de VLM/LLM/HTTP. Sin red.
- **Sin SQL en duro**: persistencia vía `select()`/`pg_insert()`; schema por Alembic.
- **Idioma**: identificadores en inglés; logs y mensajes al usuario en español.

## LLM Wiki (memoria y planificación del proyecto)

La planificación por fases, las reglas y las decisiones viven en una **LLM Wiki** (vault de Obsidian),
fuera del repo: `~/projects/Vault Projects/G-Scan-RX/` ← ajustar la ruta según la máquina.

**Antes de implementar o tocar reglas:**
1. Entrar por `G-Scan-RX/index.md` y navegar los `[[wikilinks]]` (no grep a ciegas). El plan por fase
   está en `wiki/phases/phases-index.md`.
2. Solo las reglas con `status: approved` (`wiki/rules/`) son vinculantes. Las `draft` son propuestas.
   Hoy son `approved`: cero-datos-reales, confirmacion-humana, abstencion-obligatoria,
   validacion-catalogo-obligatoria, no-objetivos (invariantes no negociables de la spec).
3. Si una regla `approved` y el código difieren, **la nota gana**.

**Al surgir lógica nueva:** usar `/ingest <regla>` — crea la nota en `wiki/` con `status: draft`, la
enlaza, registra en `log/` y corre `/lint`. **No se implementa hasta que Daniel la promueva a
`approved`.** El protocolo completo está en `G-Scan-RX/CLAUDE.md`.

## Formato de salida
- Todo código va en bloque cercado con triple backtick + lenguaje.
- Cuando el código MODIFICA algo existente, mostralo como bloque diff (`-`/`+`/contexto).
- Código totalmente nuevo va en fence normal del lenguaje, sin diff.
