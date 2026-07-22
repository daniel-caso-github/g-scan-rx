"""Evaluation harness for the prescription extraction pipeline.

Runs predictions against the golden set and reports per-field metrics.
A rise in hallucination_rate above the baseline threshold fails the
regression test (CI red).
"""

import json
from pathlib import Path
from typing import Any

from src.eval.metrics import EvalResult, calculate_metrics

GOLDEN_SET_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "golden_set"


def load_golden_set(path: Path | None = None) -> tuple[list[dict], list[dict]]:
    """Loads predictions and ground truth from the golden set directory.

    Each .jsonl file has one entry per line:
      {"prescription_id": ..., "drug": ..., "dose": ..., ...}
    Two files are expected: predictions.jsonl and ground_truth.jsonl.
    """
    directory = path or GOLDEN_SET_DIR

    pred_path = directory / "predictions.jsonl"
    gt_path = directory / "ground_truth.jsonl"

    predictions: list[dict] = []
    ground_truth: list[dict] = []

    if pred_path.exists():
        with pred_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    predictions.append(json.loads(line))

    if gt_path.exists():
        with gt_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    ground_truth.append(json.loads(line))

    return predictions, ground_truth


def evaluate(
    predictions: list[dict],
    ground_truth: list[dict],
) -> EvalResult:
    return calculate_metrics(predictions, ground_truth)


def save_result(result: EvalResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(result.summary(), f, indent=2, ensure_ascii=False)


def assert_no_regression(
    result: EvalResult,
    baseline: dict[str, Any],
) -> None:
    """Falla si alguna métrica crítica empeora respecto al baseline.

    baseline ejemplo:
        {
            "hallucination_rate_max": 0.05,
            "by_field": {
                "drug": {"exact_match_min": 0.80},
                "dose": {"exact_match_min": 0.75},
            }
        }
    """
    hr = result.total_hallucination_rate()
    hr_max = baseline.get("hallucination_rate_max", 1.0)
    assert hr <= hr_max, (
        f"Regresión detectada: hallucination_rate={hr:.4f} supera el umbral={hr_max:.4f}"
    )

    by_field = baseline.get("by_field", {})
    for f, thresholds in by_field.items():
        metrics = result.metrics_by_field.get(f)
        if metrics is None:
            continue
        if "exact_match_min" in thresholds:
            em_min = thresholds["exact_match_min"]
            em = metrics.exact_match
            assert em >= em_min, (
                f"Regresión en campo '{f}': exact_match={em:.4f} "
                f"por debajo del umbral={em_min:.4f}"
            )
