---
name: migrate
description: Genera y aplica una migración Alembic tras editar src/infrastructure/persistence/orm_models.py (schema del catálogo). Úsalo al agregar columna/tabla/índice o cambiar tipos. NO toca la BD si no hubo cambios de modelos.
---

Workflow guiado de migración del schema del catálogo.

**Argumento:** `<mensaje>` — descripción corta (ej. "add catalog dose_range", "index active_ingredient").

**Pasos en orden:**

1. **Confirmar que `orm_models.py` cambió** (`git diff src/infrastructure/persistence/orm_models.py`).
   Si no hay cambios, abortar: "¿querés correr `alembic upgrade head` solamente?".

2. **Garantizar `app-db` healthy:**
   ```bash
   docker compose up -d app-db
   until docker compose ps app-db | grep -q '(healthy)'; do sleep 2; done
   ```

3. **Autogenerar la revision:**
   ```bash
   docker compose run --rm app alembic revision --autogenerate -m "$MENSAJE"
   ```

4. **Mostrar el archivo** y revisar:
   - **Columnas `Vector(N)`** (embeddings del catálogo): verificar `import pgvector.sqlalchemy`.
   - **Índices HNSW**: `postgresql_using="hnsw"` y `postgresql_ops={"embedding": "vector_cosine_ops"}` —
     Alembic puede no autodetectarlos.

5. **Aplicar:** `docker compose run --rm app alembic upgrade head`

6. **Verificar:** `docker compose exec -T app-db psql -U app -d gscanrx -c "\d <tabla>"`

7. **Correr `/check`.**

Reglas: no editar revisions ya aplicadas (para deshacer: `alembic downgrade -1` + nueva revision).
Nunca `Base.metadata.create_all()` en código de aplicación. Ver el SQL sin aplicar: `alembic upgrade
head --sql`.
