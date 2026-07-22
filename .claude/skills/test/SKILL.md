---
name: test
description: Corre la suite de tests del proyecto dentro de Docker. Acepta opcionalmente un patrón -k para filtrar. Úsalo cuando el usuario pida correr tests, validar cambios, o iterar TDD.
---

Corre los tests del proyecto dentro del contenedor.

**Comando base:**
```bash
docker compose run --rm app pytest -v
```

**Con filtro `-k`:**
```bash
docker compose run --rm app pytest -v -k "$ARGS"
```

Reglas:
- No correr `pytest` en el host (los servicios son Docker-only; MLX es aparte y no se testea con red).
- Si falla un test, **reportar el fallo con el traceback resumido** y un diagnóstico breve. No editar
  código para "arreglar" tests sin que el usuario lo pida.
- Prestá atención a los tests de **seguridad** (abstención ante ilegible, `no_encontrado` ante fármaco
  inexistente, degradación sin levantar): si uno de esos falla, es prioritario.
- Si la imagen no está construida, sugerir `/build`. Mostrar siempre `X passed / Y failed`.
