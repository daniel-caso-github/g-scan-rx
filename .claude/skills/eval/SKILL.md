---
name: eval
description: Corre el harness de evaluación contra el golden set y reporta métricas por campo, tasa de alucinación y tasa de abstención. Es la herramienta central del proyecto — se usa antes de optimizar o afinar nada. Solo mide y reporta.
---

Corre el harness de evaluación (Fase 1, transversal). Ver `wiki/rules/eval-primero.md`.

**Argumentos:**
- `--suite <golden|smoke>` — golden set anotado (default) o un subset rápido.
- `--model <id>` — modelo/candidato a evaluar (para comparar base vs afinado vs grande genérico).

**Comando:**
```bash
docker compose run --rm app python -m src.interfaces.cli.eval --suite $SUITE [--model $MODEL]
```

Qué reporta (obligatorio, **por campo, nunca agregado a un solo número**):
- Exactitud por campo: fármaco, dosis, frecuencia, duración, vía.
- **Tasa de alucinación** (fármaco inexistente aceptado) — métrica crítica, objetivo ~0.
- **Tasa de abstención correcta** e **incorrecta** (el trade-off aceptable).
- Latencia y costo por receta (del gateway/observabilidad).
- LLM-as-judge solo para casos ambiguos, con el criterio impreso.

Reglas:
- **Solo mide**, no cambia código ni prompts.
- El golden set es de manuscritura humana **ficticia** (`cero-datos-reales`).
- Antes de cualquier optimización/fine-tuning, correr esto para tener **baseline** (idealmente 3
  modelos). Una corrida que empeore una métrica respecto al baseline es una regresión: reportarla.
- Sugerir guardar el resultado en `eval_runs/` para trazar la evolución.
