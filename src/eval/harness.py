"""Evaluation harness for the prescription extraction pipeline.

Runs predictions against the golden set and reports per-field metrics.
A rise in hallucination_rate above the baseline threshold fails the
regression test (CI red). A rise in incorrect_abstention_rate does too:
that guards against a model that games hallucination_rate by abstaining
on everything (abstencion-calibrada).

An optional LLM-as-judge can be injected to re-score cases the automatic
metric flags as ambiguous (string mismatch that may be semantically
equivalent). It is offline in tests (the judge port is mocked) and degrades
to strict string comparison on failure.
"""

import json
from pathlib import Path
from typing import Any

from src.domain.value_objects.extracted_field import FieldStatus
from src.eval.judge import LLMJudge
from src.eval.metrics import EVALUATED_FIELDS, EvalResult, _normalize, calculate_metrics

GOLDEN_SET_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "golden_set"
BASELINE_PATH = Path(__file__).parent / "baseline.json"


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


def load_baseline(path: Path | None = None) -> dict[str, Any]:
    """Loads the regression baseline (measured thresholds)."""
    baseline_path = path or BASELINE_PATH
    with baseline_path.open() as f:
        return json.load(f)


def _resolve_ambiguous_with_judge(
    predictions: list[dict],
    ground_truth: list[dict],
    judge: LLMJudge,
) -> list[dict]:
    """Rewrites predictions whose value is judged semantically equivalent.

    For each answered field that string-mismatches its (legible) ground truth,
    ask the judge. If it rules equivalent, replace the predicted value with the
    ground-truth value so the downstream metric counts it as an exact match.
    Abstained fields and unreadable ground-truth fields are left untouched.
    """
    gt_index = {gt["prescription_id"]: gt for gt in ground_truth}
    patched: list[dict] = []

    for pred in predictions:
        gt = gt_index.get(pred.get("prescription_id", ""))
        if gt is None:
            patched.append(pred)
            continue

        new_pred = dict(pred)
        gt_unreadable_map: dict = gt.get("unreadable") or {}

        for f in EVALUATED_FIELDS:
            pred_field = pred.get(f)
            gt_value = gt.get(f)
            if gt_value is None or gt_unreadable_map.get(f, False):
                continue
            if pred_field is None:
                continue
            if pred_field.get("status") in (FieldStatus.unreadable, FieldStatus.uncertain):
                continue
            if _normalize(pred_field.get("value")) == _normalize(gt_value):
                continue

            verdict = judge.is_equivalent(f, pred_field.get("value") or "", gt_value)
            if verdict.equivalent is True:
                patched_field = dict(pred_field)
                patched_field["value"] = gt_value
                new_pred[f] = patched_field

        patched.append(new_pred)

    return patched


def evaluate(
    predictions: list[dict],
    ground_truth: list[dict],
    judge: LLMJudge | None = None,
) -> EvalResult:
    if judge is not None:
        predictions = _resolve_ambiguous_with_judge(predictions, ground_truth, judge)
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
            "incorrect_abstention_rate_max": 0.30,
            "by_field": {
                "drug": {"exact_match_min": 0.80, "incorrect_abstention_rate_max": 0.20},
                "dose": {"exact_match_min": 0.75},
            }
        }
    """
    hr = result.total_hallucination_rate()
    hr_max = baseline.get("hallucination_rate_max", 1.0)
    assert hr <= hr_max, (
        f"Regresión detectada: hallucination_rate={hr:.4f} supera el umbral={hr_max:.4f}"
    )

    iar = result.total_incorrect_abstention_rate()
    iar_max = baseline.get("incorrect_abstention_rate_max", 1.0)
    assert iar <= iar_max, (
        f"Regresión detectada: incorrect_abstention_rate={iar:.4f} "
        f"supera el umbral={iar_max:.4f} (el modelo se abstiene de más)"
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
        if "incorrect_abstention_rate_max" in thresholds:
            field_iar_max = thresholds["incorrect_abstention_rate_max"]
            field_iar = metrics.incorrect_abstention_rate
            assert field_iar <= field_iar_max, (
                f"Regresión en campo '{f}': incorrect_abstention_rate={field_iar:.4f} "
                f"supera el umbral={field_iar_max:.4f}"
            )
