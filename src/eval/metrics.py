"""Per-field evaluation metrics for the extraction pipeline.

Metrics are always reported PER FIELD, never aggregated into a single number.
Evaluated fields: drug, dose, frequency, duration, route.

Key metrics:
- exact_match: extracted value == ground truth (normalized)
- abstention_rate: fraction of fields marked unreadable/uncertain
- hallucination_rate: fraction of incorrect extractions where the system
  did not abstain (the costliest error per abstencion-obligatoria)
- correct_abstention_rate: fraction of abstentions that were RIGHT (the field
  is genuinely unreadable in the ground truth) over all genuinely-unreadable
  fields
- incorrect_abstention_rate: fraction of abstentions that were WRONG (the field
  was legible in the ground truth but the system abstained) over all
  genuinely-legible fields
- precision: TP / (TP + FP) over fields where the system gave an answer
- recall: TP / (TP + FN) over all ground-truth fields

Calibrated abstention (abstencion-calibrada): a model that abstains on
EVERYTHING scores hallucination_rate=0.0 but incorrect_abstention_rate=1.0.
Separating correct from incorrect abstention is what keeps that degenerate
model from silently passing the regression gate.
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
    # Abstention broken down by ground-truth legibility:
    legible_total: int = 0  # ground-truth fields that ARE legible
    unreadable_total: int = 0  # ground-truth fields that are genuinely unreadable
    correct_abstentions: int = 0  # abstained AND ground-truth is unreadable
    incorrect_abstentions: int = 0  # abstained BUT ground-truth is legible

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
    def correct_abstention_rate(self) -> float:
        """Of the genuinely-unreadable fields, how many did the system abstain on.

        High is good: the system recognizes the illegible as illegible.
        """
        if self.unreadable_total == 0:
            return 0.0
        return self.correct_abstentions / self.unreadable_total

    @property
    def incorrect_abstention_rate(self) -> float:
        """Of the genuinely-legible fields, how many did the system wrongly abstain on.

        Low is good: abstaining on something that was actually readable is a
        recall cost. This is the metric that catches the "abstain on everything"
        degenerate model.
        """
        if self.legible_total == 0:
            return 0.0
        return self.incorrect_abstentions / self.legible_total

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
            "correct_abstention_rate": round(self.correct_abstention_rate, 4),
            "incorrect_abstention_rate": round(self.incorrect_abstention_rate, 4),
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

    def total_incorrect_abstention_rate(self) -> float:
        """Aggregate wrong-abstention rate across all fields.

        Guards against a model that abstains globally to game hallucination_rate.
        """
        total_legible = sum(m.legible_total for m in self.metrics_by_field.values())
        total_incorrect = sum(
            m.incorrect_abstentions for m in self.metrics_by_field.values()
        )
        return total_incorrect / total_legible if total_legible > 0 else 0.0


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return value.lower().strip()


def _is_abstention(pred_field: dict | None) -> bool:
    if pred_field is None:
        return True
    return pred_field.get("status") in (
        FieldStatus.unreadable,
        FieldStatus.uncertain,
    )


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
                      An optional "unreadable" key holds a per-field map
                      {field_name: bool} marking which fields are GENUINELY
                      illegible in the source image. When a field is marked
                      unreadable, its ground-truth value is expected to be None
                      and abstaining on it counts as a CORRECT abstention.
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

        gt_unreadable_map: dict = gt.get("unreadable") or {}

        for f in EVALUATED_FIELDS:
            metrics = result.metrics_by_field[f]

            pred_field = pred.get(f)
            gt_value = gt.get(f)
            gt_unreadable = bool(gt_unreadable_map.get(f, False))

            # A field that neither applies nor is marked unreadable is skipped.
            if gt_value is None and not gt_unreadable:
                continue

            metrics.total += 1
            abstained = _is_abstention(pred_field)

            if gt_unreadable:
                # Ground truth says this field is genuinely illegible.
                metrics.unreadable_total += 1
                if abstained:
                    metrics.abstained += 1
                    metrics.correct_abstentions += 1
                else:
                    # System asserted a value on something illegible: a
                    # hallucination (invented a plausible value).
                    metrics.hallucinations += 1
                continue

            # Ground truth field is legible.
            metrics.legible_total += 1

            if abstained:
                metrics.abstained += 1
                metrics.incorrect_abstentions += 1
                continue

            pred_value = _normalize(pred_field.get("value"))
            gt_normalized = _normalize(gt_value)

            if pred_value == gt_normalized:
                metrics.exact += 1
            else:
                metrics.hallucinations += 1

    return result
