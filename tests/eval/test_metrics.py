"""Regression tests for the evaluation harness.

Verify that metrics are calculated correctly and that abstention invariants
are maintained. In CI, a hallucination_rate above the baseline threshold
fails the test.
"""

import pytest

from src.domain.value_objects.extracted_field import FieldStatus
from src.eval.harness import assert_no_regression, evaluate
from src.eval.metrics import EVALUATED_FIELDS, calculate_metrics


def _pred(prescription_id: str, **fields) -> dict:
    """Helper: builds a serialized prediction."""
    result = {"prescription_id": prescription_id}
    for f in EVALUATED_FIELDS:
        value = fields.get(f)
        if value is None:
            result[f] = {"status": FieldStatus.unreadable, "value": None}
        elif value == "__uncertain__":
            result[f] = {"status": FieldStatus.uncertain, "value": None}
        else:
            result[f] = {"status": FieldStatus.readable, "value": value}
    return result


def _gt(prescription_id: str, unreadable: dict | None = None, **fields) -> dict:
    row = {"prescription_id": prescription_id, **fields}
    if unreadable is not None:
        row["unreadable"] = unreadable
    return row


class TestCalculateMetrics:
    def test_all_correct(self):
        preds = [_pred("p1", drug="amoxicilina", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        for f in EVALUATED_FIELDS:
            m = result.metrics_by_field[f]
            assert m.exact_match == 1.0
            assert m.hallucination_rate == 0.0

    def test_abstentions_not_counted_as_hallucination(self):
        preds = [_pred("p1", drug=None, dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        drug_m = result.metrics_by_field["drug"]
        assert drug_m.abstained == 1
        assert drug_m.hallucinations == 0
        assert drug_m.hallucination_rate == 0.0

    def test_incorrect_value_counted_as_hallucination(self):
        preds = [_pred("p1", drug="ibuprofeno", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        drug_m = result.metrics_by_field["drug"]
        assert drug_m.hallucinations == 1
        assert drug_m.hallucination_rate == 1.0

    def test_multiple_prescriptions(self):
        preds = [
            _pred("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral"),
            _pred("p2", drug="ibuprofeno", dose="400 mg",
                   frequency="cada 12 horas", duration="5 días", route="oral"),
        ]
        gt = [
            _gt("p1", drug="amoxicilina", dose="500 mg",
                 frequency="cada 8 horas", duration="7 días", route="oral"),
            _gt("p2", drug="ibuprofeno", dose="400 mg",
                 frequency="cada 12 horas", duration="5 días", route="oral"),
        ]
        result = calculate_metrics(preds, gt)
        for f in EVALUATED_FIELDS:
            m = result.metrics_by_field[f]
            assert m.total == 2
            assert m.exact == 2

    def test_uncertain_counted_as_abstention(self):
        preds = [_pred("p1", drug="__uncertain__", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        drug_m = result.metrics_by_field["drug"]
        assert drug_m.abstained == 1
        assert drug_m.hallucinations == 0

    def test_total_hallucination_rate(self):
        preds = [_pred("p1", drug="ibuprofeno", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        hr = result.total_hallucination_rate()
        assert hr > 0.0


class TestAssertNoRegression:
    def test_passes_below_threshold(self):
        preds = [_pred("p1", drug="amoxicilina", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = evaluate(preds, gt)
        assert_no_regression(result, {"hallucination_rate_max": 0.05})

    def test_fails_above_threshold(self):
        preds = [_pred("p1", drug="ibuprofeno", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = evaluate(preds, gt)
        with pytest.raises(AssertionError, match="Regresión detectada"):
            assert_no_regression(result, {"hallucination_rate_max": 0.05})

    def test_fails_due_to_low_exact_match(self):
        preds = [_pred("p1", drug="ibuprofeno", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = evaluate(preds, gt)
        with pytest.raises(AssertionError, match="Regresión en campo 'drug'"):
            assert_no_regression(
                result,
                {"hallucination_rate_max": 1.0, "by_field": {"drug": {"exact_match_min": 0.9}}},
            )


class TestCalibratedAbstention:
    """Correct vs incorrect abstention (abstencion-calibrada)."""

    def test_correct_abstention_when_ground_truth_unreadable(self):
        # Field is genuinely illegible; system abstains -> CORRECT.
        preds = [_pred("p1", drug=None, dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug=None, dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral",
                   unreadable={"drug": True})]
        result = calculate_metrics(preds, gt)
        drug_m = result.metrics_by_field["drug"]
        assert drug_m.correct_abstentions == 1
        assert drug_m.incorrect_abstentions == 0
        assert drug_m.correct_abstention_rate == 1.0
        assert drug_m.incorrect_abstention_rate == 0.0
        assert drug_m.hallucination_rate == 0.0

    def test_incorrect_abstention_when_ground_truth_legible(self):
        # Field is legible; system abstains -> INCORRECT.
        preds = [_pred("p1", drug=None, dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        drug_m = result.metrics_by_field["drug"]
        assert drug_m.incorrect_abstentions == 1
        assert drug_m.correct_abstentions == 0
        assert drug_m.incorrect_abstention_rate == 1.0
        assert drug_m.correct_abstention_rate == 0.0

    def test_hallucination_when_asserting_on_unreadable_field(self):
        # Ground truth illegible but system asserts a value -> hallucination.
        preds = [_pred("p1", drug="amoxicilina", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug=None, dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral",
                   unreadable={"drug": True})]
        result = calculate_metrics(preds, gt)
        drug_m = result.metrics_by_field["drug"]
        assert drug_m.hallucinations == 1
        assert drug_m.correct_abstentions == 0

    def test_abstain_on_everything_does_not_pass_gate(self):
        # The degenerate model: abstains on every field. hallucination_rate=0
        # but incorrect_abstention_rate=1.0 -> must be caught.
        preds = [_pred("p1")]  # all fields None -> abstained
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        assert result.total_hallucination_rate() == 0.0
        assert result.total_incorrect_abstention_rate() == 1.0
        with pytest.raises(AssertionError, match="incorrect_abstention_rate"):
            assert_no_regression(
                result,
                {"hallucination_rate_max": 0.05, "incorrect_abstention_rate_max": 0.30},
            )

    def test_to_dict_reports_both_abstention_rates(self):
        preds = [_pred("p1", drug="amoxicilina", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        d = calculate_metrics(preds, gt).metrics_by_field["drug"].to_dict()
        assert "correct_abstention_rate" in d
        assert "incorrect_abstention_rate" in d

    def test_per_field_incorrect_abstention_threshold(self):
        preds = [_pred("p1", drug=None, dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = calculate_metrics(preds, gt)
        with pytest.raises(AssertionError, match="Regresión en campo 'drug'"):
            assert_no_regression(
                result,
                {
                    "hallucination_rate_max": 1.0,
                    "by_field": {"drug": {"incorrect_abstention_rate_max": 0.5}},
                },
            )
