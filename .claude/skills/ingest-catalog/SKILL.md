---
name: ingest-catalog
description: Ingesta el catálogo oficial de medicamentos (CIMA o DIGEMID) a Postgres+pgvector como ItemCatalogo, con upsert idempotente y cálculo de embeddings. Úsalo para cargar/actualizar la fuente de verdad de la verificación. --dry-run solo imprime.
---

Ejecuta el `IngestCatalogUseCase` sobre una fuente de catálogo.

**Argumentos:**
- `<source>` — `cima` (España) o `digemid` (Perú). El primario está por decidir (`decisiones-pendientes`).
- `--limit N` — máx de ítems (opcional; útil para smoke).
- `--dry-run` — imprime los `ItemCatalogo` normalizados sin tocar la BD.

**Comando:**
```bash
# Persistiendo (requiere docker compose up -d app-db):
docker compose run --rm app python -m src.interfaces.cli.ingest_catalog --source $SOURCE [--limit N]

# Solo imprimir:
docker compose run --rm app python -m src.interfaces.cli.ingest_catalog --source $SOURCE --limit N --dry-run
```

Reglas:
- Antes de codear una fuente nueva, validá términos de uso (atribución, reutilización de datos).
  Ver `wiki/sources/cima-aemps.md` / `digemid.md`.
- Ingesta **idempotente**: `make_id(source, code)` + `on_conflict_do_update`. Reingerir no duplica.
- Calcula el `embedding` de nombre+presentación para `recuperacion-hibrida` (índice HNSW).
- Con `--dry-run`, validar que cada ítem trae `active_ingredient`, `presentation`, `source`.
- Es la fuente de verdad de `validacion-catalogo-obligatoria`: si la ingesta falla parcial, reportar
  cuántos ítems entraron y cuáles no.
