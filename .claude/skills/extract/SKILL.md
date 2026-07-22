---
name: extract
description: Corre el pipeline de visión + normalización sobre una imagen de receta (sintética o ficticia) y muestra los campos extraídos con su confianza y estado de abstención. Úsalo para validar la extracción sobre datos de prueba. NUNCA con recetas reales de pacientes.
---

Pipeline de extracción (Fase 3) sobre una imagen de receta.

**Pre-requisito**: catálogo cargado (`/ingest-catalog`) para poder verificar; normalizador disponible
(host MLX o fallback nube).

**Argumentos:**
- `<img>` — ruta a una imagen **sintética o de contenido ficticio** (`data/synthetic/…` o el golden
  set). **Nunca** una receta real (`cero-datos-reales`).
- `--print` — imprime por campo: valor, confianza, `status` (legible/dudoso/ilegible) y veredicto.

**Comando:**
```bash
docker compose run --rm app python -m src.interfaces.cli.extract --image "$IMG" [--print]
```

Reglas:
- La salida debe mostrar la **confianza por campo** y qué se **abstuvo** — ese es el punto, no el
  texto plano (`abstencion-calibrada`).
- Todo campo debe traer un `veredicto-verificacion` (contra catálogo). Si el verificador está caído,
  el campo cae a `dudoso`, no rompe.
- Para iterar el prompt de visión/normalización: editarlo en `src/infrastructure/vision/` o
  `normalizer/` y volver a correr (los servicios van por volumen; no hace falta rebuild).
- Recordá: la salida real va a **confirmación humana** campo por campo; este skill es para debug.
