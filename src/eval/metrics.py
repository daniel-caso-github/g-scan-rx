"""Per-field evaluation metrics for the extraction pipeline.

Metrics are always reported PER FIELD, never aggregated into a single number.
Evaluated fields: drug, dose, frequency, duration, route.

Key metrics:
- exact_match: extracted value == ground truth (normalized)
- abstention_rate: fraction of fields marked unreadable/uncertain
- hallucination_rate: fraction of incorrect extractions where the system
  did not abstain (the costliest error per abstencion-obligatoria)
- precision: TP / (TP + FP) over fields where the system gave an answer
- recall: TP / (TP + FN) over all ground-truth fields
"""

from dataclasses import dataclass, field

from src.domain.value_objects.extracted_field import FieldStatus

EVALUATED_FIELDS = ("drug", "dose", "frequency", "duration", "route")


@dataclass
class FieldMetrics:
    field: str
    total: int = 0
    exact: int = 0
    abstained: int = 0
    hallucinations: int = 0  # incorrect value extracted without abstaining

    @property
    def exact_match(self) -> float:
        answered = self.total - self.abstained
        return self.exact / answered if answered > 0 else 0.0

    @property
    def abstention_rate(self) -> float:
        return self.abstained / self.total if self.total > 0 else 0.0

    @property
    def hallucination_rate(self) -> float:
        answered = self.total - self.abstained
        return self.hallucinations / answered if answered > 0 else 0.0

    @property
    def precision(self) -> float:
        answered = self.total - self.abstained
        if answered == 0:
            return 1.0
        return self.exact / answered

    @property
    def recall(self) -> float:
        return self.exact / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "total": self.total,
            "exact_match": round(self.exact_match, 4),
            "abstention_rate": round(self.abstention_rate, 4),
            "hallucination_rate": round(self.hallucination_rate, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
        }


@dataclass
class EvalResult:
    metrics_by_field: dict[str, FieldMetrics] = field(default_factory=dict)

    def summary(self) -> list[dict]:
        return [m.to_dict() for m in self.metrics_by_field.values()]

    def total_hallucination_rate(self) -> float:
        total_answered = sum(
            m.total - m.abstained for m in self.metrics_by_field.values()
        )
        total_hallucinations = sum(m.hallucinations for m in self.metrics_by_field.values())
        return total_hallucinations / total_answered if total_answered > 0 else 0.0


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return value.lower().strip()


def calculate_metrics(
    predictions: list[dict],
    ground_truth: list[dict],
) -> EvalResult:
    """Calculates per-field metrics comparing predictions against ground truth.

    Args:
        predictions: list of dicts with fields {prescription_id, drug, dose, ...}
                     where each value is a serialized ExtractedField or None.
        ground_truth: list of dicts with the same fields but the correct value
                      as a string (or None if that field does not apply).
    """
    result = EvalResult(
        metrics_by_field={f: FieldMetrics(field=f) for f in EVALUATED_FIELDS}
    )

    gt_index: dict[str, dict] = {gt["prescription_id"]: gt for gt in ground_truth}

    for pred in predictions:
        prescription_id = pred.get("prescription_id", "")
        gt = gt_index.get(prescription_id)
        if gt is None:
            continue

        for f in EVALUATED_FIELDS:
            metrics = result.metrics_by_field[f]
            metrics.total += 1

            pred_field = pred.get(f)
            gt_value = gt.get(f)

            if gt_value is None:
                metrics.total -= 1
                continue

            if pred_field is None or pred_field.get("status") in (
                FieldStatus.unreadable,
                FieldStatus.uncertain,
            ):
                metrics.abstained += 1
                continue

            pred_value = _normalize(pred_field.get("value"))
            gt_normalized = _normalize(gt_value)

            if pred_value == gt_normalized:
                metrics.exact += 1
            else:
                metrics.hallucinations += 1

    return result
