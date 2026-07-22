---
name: review
description: Code review del diff actual contra las convenciones del proyecto (seguridad del paciente, abstención, validación contra catálogo, Pydantic v2, idempotencia, fixtures offline). Úsalo antes de un commit o tras implementar una feature. Solo reporta.
---

Code review del diff actual del repositorio usando las convenciones de G-Scan-RX.

**Paso 1 — obtener el diff:**
```bash
git diff HEAD
# si no hay diff sin commit:
git diff main...HEAD
```
Si no hay cambios, reportarlo y terminar.

**Paso 2 — checklist:**

### Críticos (bloquean merge) — seguridad del paciente
- [ ] Ningún camino acepta un valor de baja confianza sin abstención (`abstencion-obligatoria`).
- [ ] Ningún campo llega a la ficha sin validación contra catálogo (`validacion-catalogo-obligatoria`).
- [ ] No hay atajo que salte la confirmación humana (`confirmacion-humana`).
- [ ] Cero datos reales de pacientes en código/fixtures (`cero-datos-reales`).
- [ ] Los adaptadores de modelo (VLM/normalizador/verificador) **no levantan** hacia el pipeline;
      degradan a `dudoso`.

### Importantes
- [ ] Modelos con **Pydantic v2** (no dataclasses/dicts crudos).
- [ ] IDs idempotentes con `make_id`; ingesta del catálogo con upsert.
- [ ] Clientes HTTP/LLM/VLM con `tenacity` retries.
- [ ] Sin `text()`/SQL en duro; schema por Alembic.
- [ ] Sin comentarios/docstrings inventados; identificadores en inglés, mensajes en español.

### Estilo
- [ ] `ruff check` pasaría. Funciones < 50 líneas; archivos < 300 (suave).

**Paso 3 — reportar** por severidad con `archivo:línea — issue → sugerencia`. **No aplicar cambios.**
Si todo pasa, decirlo y mencionar 1-2 fortalezas.
