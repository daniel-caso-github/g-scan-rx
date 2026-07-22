"""Harness de evaluación para el pipeline de extracción de recetas.

Corre predicciones contra el golden set y reporta métricas por campo.
Una caída en la tasa de alucinación hace fallar el test de regresión (CI rojo).
"""

import json
from pathlib import Path
from typing import Any

from src.eval.metrics import ResultadoEval, calcular_metricas

GOLDEN_SET_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "golden_set"


def cargar_golden_set(path: Path | None = None) -> tuple[list[dict], list[dict]]:
    """Carga predicciones y ground truth desde el directorio del golden set.

    Cada archivo .jsonl tiene una entrada por línea con:
      {"receta_id": ..., "farmaco": ..., "dosis": ..., ...}
    Se esperan dos archivos: predictions.jsonl y ground_truth.jsonl.
    """
    directorio = path or GOLDEN_SET_DIR

    pred_path = directorio / "predictions.jsonl"
    gt_path = directorio / "ground_truth.jsonl"

    predicciones: list[dict] = []
    ground_truth: list[dict] = []

    if pred_path.exists():
        with pred_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    predicciones.append(json.loads(line))

    if gt_path.exists():
        with gt_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    ground_truth.append(json.loads(line))

    return predicciones, ground_truth


def evaluar(
    predicciones: list[dict],
    ground_truth: list[dict],
) -> ResultadoEval:
    return calcular_metricas(predicciones, ground_truth)


def guardar_resultado(resultado: ResultadoEval, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(resultado.resumen(), f, indent=2, ensure_ascii=False)


def assert_sin_regresion(
    resultado: ResultadoEval,
    baseline: dict[str, Any],
) -> None:
    """Falla si alguna métrica crítica empeora respecto al baseline.

    baseline ejemplo:
        {
            "hallucination_rate_max": 0.05,
            "por_campo": {
                "farmaco": {"exact_match_min": 0.80},
                "dosis": {"exact_match_min": 0.75},
            }
        }
    """
    hr = resultado.hallucination_rate_total()
    hr_max = baseline.get("hallucination_rate_max", 1.0)
    assert hr <= hr_max, (
        f"Regresión detectada: hallucination_rate={hr:.4f} supera el umbral={hr_max:.4f}"
    )

    por_campo = baseline.get("por_campo", {})
    for campo, umbrales in por_campo.items():
        metrica = resultado.metricas_por_campo.get(campo)
        if metrica is None:
            continue
        if "exact_match_min" in umbrales:
            em_min = umbrales["exact_match_min"]
            em = metrica.exact_match
            assert em >= em_min, (
                f"Regresión en campo '{campo}': exact_match={em:.4f} "
                f"por debajo del umbral={em_min:.4f}"
            )
