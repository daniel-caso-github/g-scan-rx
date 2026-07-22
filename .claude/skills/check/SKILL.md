---
name: check
description: Gate pre-commit. Corre pytest + ruff en una sola pasada dentro de Docker y reporta el primer fallo de cada uno. Úsalo cuando el usuario pida validar antes de commit, "is it ready", o al terminar una feature.
---

Validación combinada antes de commit: tests + lint.

**Comandos:**
```bash
docker compose run --rm app pytest -v
docker compose run --rm app ruff check src tests
```

Reglas:
- Correr los dos siempre, aunque el primero falle (queremos el panorama completo).
- Reportar el **primer fallo** de cada uno con una sentencia accionable.
- Si ruff reporta múltiples issues, agrupar por regla y sugerir `ruff check --fix` solo para fixes
  automáticos seguros (NO `--unsafe-fixes`).
- Si todo pasa: `✓ pytest N passed | ✓ ruff clean`.
- No correr `pytest`/`ruff` en el host — solo dentro del contenedor.
