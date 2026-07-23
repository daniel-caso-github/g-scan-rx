# Golden set

Conjunto de referencia para el harness de evaluación (`src/eval/`). Es la base
sobre la que se mide alucinación, abstención calibrada y regresión de
prompts/modelos **antes** de cualquier optimización o fine-tuning
(regla `eval-primero`).

> Estado: **infraestructura + set SEMILLA sintético listos**. El llenado
> completo con imágenes manuscritas ficticias (100-200 recetas) queda
> **pendiente** — ver "Pendiente" abajo.

## Reglas que aplican

- **cero-datos-reales**: NUNCA recetas reales de pacientes ni PII real. Todo
  ficticio/sintético. Nombres, dosis y textos inventados o derivados del
  catálogo semilla.
- **abstencion-calibrada**: cada campo del ground truth declara si es
  *genuinamente ilegible* en la imagen fuente. Abstenerse ahí es CORRECTO;
  abstenerse en un campo legible es un error de recall.

## Formato

Dos archivos JSONL, una entrada por línea, emparejados por `prescription_id`.

### `predictions.jsonl`

Salida del pipeline (VLM → normalizador). Un objeto por receta; cada campo
evaluado (`drug`, `dose`, `frequency`, `duration`, `route`) es un
`ExtractedField` serializado:

```json
{
  "prescription_id": "801dcd905cfb67907c9b8c55",
  "drug": {
    "value": "losartan",
    "confidence": 0.91,
    "status": "readable",
    "source_crop": {"bbox": [12, 40, 220, 32], "crop_ref": "crop_12_40_220_32.png"}
  },
  "dose": { "value": "50 mg", "confidence": 0.88, "status": "readable", "source_crop": {...} }
}
```

`status` ∈ `readable` | `uncertain` | `unreadable`. `uncertain` y `unreadable`
cuentan como **abstención** en las métricas. Un campo `unreadable` lleva
`value: null`.

### `ground_truth.jsonl`

Anotación humana campo por campo. El valor correcto es un **string** (o `null`
si el campo es ilegible). Incluye el mapa `unreadable`:

```json
{
  "prescription_id": "801dcd905cfb67907c9b8c55",
  "drug": "losartan",
  "dose": "50 mg",
  "frequency": "cada 12 horas",
  "duration": "7 días",
  "route": "sublingual",
  "unreadable": {
    "drug": false, "dose": false, "frequency": false,
    "duration": false, "route": false
  }
}
```

**`unreadable[campo] = true`** marca un campo *genuinamente ilegible* en la
imagen fuente (letra intrazable, tachado, cortado). En ese caso el `value` de
ese campo va en `null`. Es el eje del proyecto: distingue la abstención
**correcta** (el campo era ilegible) de la **incorrecta** (el campo era legible
pero el sistema se abstuvo). Ver `src/eval/metrics.py`:
`correct_abstention_rate` / `incorrect_abstention_rate`.

## Cómo se llena (proceso manual, pendiente)

1. Generar/dibujar **100-200 recetas manuscritas FICTICIAS** (cero datos reales).
   Pueden ser escritas a mano por personas, o sintetizadas, siempre inventadas.
2. Pasar cada imagen por el pipeline y volcar su salida a `predictions.jsonl`.
3. Anotar el `ground_truth.jsonl` a mano campo por campo:
   - valor correcto cuando el campo es legible;
   - `value: null` + `unreadable[campo]=true` cuando el campo es realmente
     ilegible en la imagen (criterio del anotador, no del modelo).
4. Incluir a propósito casos con campos ilegibles y casos ambiguos
   (sinónimos/abreviaturas: `c/8h` vs `cada 8 horas`) para ejercitar el
   LLM-as-judge (`src/eval/judge.py`).
5. Regenerar el baseline: `python -m src.eval.build_baseline`.

## Set SEMILLA (lo que hay hoy)

Los `.jsonl` actuales son un set **sintético** de 15 recetas generado con
`src/data/synthetic/generator.py`, para que el harness, el baseline y el gate de
regresión funcionen desde ya. Incluye campos marcados `unreadable` y campos
`uncertain` (abstenciones incorrectas). **No sustituye** al golden set real de
imágenes manuscritas.

Regenerar el set semilla (determinista):

```bash
docker compose run --rm app python -m src.eval.seed_golden_set --n 15
docker compose run --rm app python -m src.eval.build_baseline
```

## Pendiente

- [ ] 100-200 recetas manuscritas ficticias con sus imágenes.
- [ ] Anotación humana campo por campo (incl. `unreadable`).
- [ ] Casos ambiguos etiquetados para el LLM-as-judge.
- [ ] Regenerar `baseline.json` con las métricas medidas sobre el set real.
