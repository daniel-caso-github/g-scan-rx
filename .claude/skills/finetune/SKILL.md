---
name: finetune
description: Afina el normalizador local (o un VLM pequeño) con MLX en el host Apple Silicon (LoRA 4-bit). Úsalo en Fase 4, SOLO después de tener baseline con /eval. Corre en el host, no en Docker.
---

Fine-tuning con MLX en el **host** (Mac Mini M3 Pro, 18 GB). **No** corre en Docker.

**Pre-requisitos duros:**
- Baseline ya medido con `/eval` (`eval-primero`). Sin baseline, frená y avisá.
- Dataset de entrenamiento generado desde `datos-sinteticos` (nunca datos reales).
- Ampliar memoria GPU antes de entrenar: `sudo sysctl iogpu.wired_limit_mb=14336`.
- **Nada más levantado**: bajar Postgres/reranker/embeddings pesados (consumen 4-6 GB).

**Argumentos:**
- `<exp>` — `exp-a` (normalizador texto→JSON, `mlx-lm`) o `exp-b` (VLM pequeño, `mlx-vlm`).
- `--model <base>` — modelo base (Qwen3 4B / Llama 3.2 3B / Gemma 3 4B; ver `decisiones-pendientes`).

**Comandos (host):**
```bash
# Experimento A — normalizador (LoRA):
python -m mlx_lm.lora --model "$BASE" --train --data data/norm --iters 1000 --batch-size 1

# Experimento B — VLM pequeño:
python -m mlx_vlm.lora --model "$BASE" --train --data data/vlm ...

# Servir el afinado (API OpenAI-compatible) para /extract y /eval:
mlx_lm.server --model models/normalizer-lora
```

Reglas:
- Entrenar en aislamiento; desarrollar con el modelo ya afinado y cuantizado.
- Al terminar, **medir con `/eval`** base vs afinado vs grande genérico y **documentar el trade-off**
  (haya o no mejora — ese es el entregable).
- Opcional: contraste de servido MLX (Apple Silicon) vs vLLM (RTX 5090) — latencia/throughput.
