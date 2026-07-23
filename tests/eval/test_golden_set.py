"""Tests for the seed golden set builder and the shipped golden set + baseline.

These lock in that:
- the seed builder produces well-formed prediction/ground-truth rows including
  the `unreadable` map (abstencion-calibrada), and
- the shipped golden set passes its own measured baseline (no regression on the
  reference data itself).
"""

from src.eval.build_baseline import build_baseline
from src.eval.harness import assert_no_regression, evaluate, load_baseline, load_golden_set
from src.eval.metrics import EVALUATED_FIELDS
from src.eval.seed_golden_set import build_rows, generate_seed_set


class TestSeedBuilder:
    def test_generate_seed_set_writes_files(self, tmp_path):
        preds, gt = generate_seed_set(n=8, seed=7, output_dir=tmp_path)
        assert len(preds) == 8
        assert len(gt) == 8
        assert (tmp_path / "predictions.jsonl").exists()
        assert (tmp_path / "ground_truth.jsonl").exists()

    def test_rows_are_paired_and_have_all_fields(self, tmp_path):
        preds, gt = generate_seed_set(n=6, seed=3, output_dir=tmp_path)
        pred_ids = {p["prescription_id"] for p in preds}
        gt_ids = {g["prescription_id"] for g in gt}
        assert pred_ids == gt_ids
        for row in gt:
            assert "unreadable" in row
            for f in EVALUATED_FIELDS:
                assert f in row
                assert f in row["unreadable"]

    def test_unreadable_ground_truth_has_null_value(self, tmp_path):
        _, gt = generate_seed_set(n=40, seed=1, output_dir=tmp_path)
        for row in gt:
            for f in EVALUATED_FIELDS:
                if row["unreadable"].get(f):
                    assert row[f] is None

    def test_deterministic_with_same_seed(self, catalog):
        from src.data.synthetic.generator import PrescriptionGenerator

        g1 = PrescriptionGenerator(catalog=catalog, seed=55)
        g2 = PrescriptionGenerator(catalog=catalog, seed=55)
        p1, gt1 = build_rows(g1.generate(n=5))
        p2, gt2 = build_rows(g2.generate(n=5))
        assert [r["prescription_id"] for r in p1] == [r["prescription_id"] for r in p2]
        assert gt1 == gt2

    def test_seed_set_exercises_calibrated_abstention(self, tmp_path):
        # With enough samples we get both correct and incorrect abstentions.
        preds, gt = generate_seed_set(n=50, seed=20260722, output_dir=tmp_path)
        result = evaluate(preds, gt)
        total_correct = sum(m.correct_abstentions for m in result.metrics_by_field.values())
        total_incorrect = sum(
            m.incorrect_abstentions for m in result.metrics_by_field.values()
        )
        assert total_correct >= 1
        assert total_incorrect >= 1


class TestShippedGoldenSetAndBaseline:
    def test_golden_set_loads(self):
        preds, gt = load_golden_set()
        assert len(preds) > 0
        assert len(gt) > 0

    def test_baseline_loads_and_has_new_thresholds(self):
        baseline = load_baseline()
        assert "hallucination_rate_max" in baseline
        assert "incorrect_abstention_rate_max" in baseline
        assert "by_field" in baseline

    def test_shipped_set_passes_its_baseline(self):
        preds, gt = load_golden_set()
        result = evaluate(preds, gt)
        assert_no_regression(result, load_baseline())

    def test_build_baseline_matches_measurements(self):
        # The builder must not produce a baseline the reference data fails.
        preds, gt = load_golden_set()
        result = evaluate(preds, gt)
        assert_no_regression(result, build_baseline())
