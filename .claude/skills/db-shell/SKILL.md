---
name: db-shell
description: Abre un psql interactivo contra app-db (Postgres+pgvector con el catálogo de medicamentos). Para exploración ad-hoc, debug, o verificar el estado del catálogo. NO para cambios estructurales — ésos van por Alembic con /migrate.
---

Shell SQL ad-hoc al servicio `app-db` (catálogo de medicamentos).

**Interactivo:**
```bash
docker compose exec app-db psql -U app -d gscanrx
```

**Single-shot:**
```bash
docker compose exec -T app-db psql -U app -d gscanrx -c "$QUERY"
```

**Recetas útiles:**
```sql
\dt
SELECT * FROM alembic_version;

-- Tamaño del catálogo por fuente
SELECT source, count(*) FROM catalog_items GROUP BY source;

-- Verificar extensión pgvector
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Definición e índices de catalog_items (incl. HNSW)
\d catalog_items

-- Buscar un principio activo
SELECT id, active_ingredient, brand_name, presentation, source
FROM catalog_items WHERE active_ingredient ILIKE '%amoxicilina%' LIMIT 10;
```

**Reglas:**
- **No** `CREATE/ALTER/DROP TABLE`, `CREATE INDEX` desde aquí. Schema por Alembic (`/migrate`).
- **No** mutar `alembic_version` a mano.
- Permitido: SELECTs, EXPLAIN, `\d`, `\dt`, `\di`, y UPDATE/DELETE de datos de prueba en desarrollo.
- Si `app-db` no corre: `docker compose up -d app-db`.
