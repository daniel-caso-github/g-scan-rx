"""Tests for the LLM-as-judge (offline: the client port is mocked)."""

from src.domain.value_objects.extracted_field import FieldStatus
from src.eval.harness import evaluate
from src.eval.judge import JudgeVerdict, LLMJudge, LLMJudgeClient
from src.eval.metrics import EVALUATED_FIELDS


class _StubClient(LLMJudgeClient):
    def __init__(self, verdict: JudgeVerdict) -> None:
        self._verdict = verdict
        self.calls: list[tuple[str, str, str]] = []

    def judge(self, field: str, predicted: str, ground_truth: str) -> JudgeVerdict:
        self.calls.append((field, predicted, ground_truth))
        return self._verdict


class _RaisingClient(LLMJudgeClient):
    def judge(self, field: str, predicted: str, ground_truth: str) -> JudgeVerdict:
        raise RuntimeError("boom")


def _pred(prescription_id: str, **fields) -> dict:
    result = {"prescription_id": prescription_id}
    for f in EVALUATED_FIELDS:
        value = fields.get(f)
        if value is None:
            result[f] = {"status": FieldStatus.unreadable, "value": None}
        else:
            result[f] = {"status": FieldStatus.readable, "value": value}
    return result


def _gt(prescription_id: str, **fields) -> dict:
    return {"prescription_id": prescription_id, **fields}


class TestLLMJudge:
    def test_returns_client_verdict(self):
        judge = LLMJudge(_StubClient(JudgeVerdict(equivalent=True, rationale="ok")))
        verdict = judge.is_equivalent("frequency", "c/8h", "cada 8 horas")
        assert verdict.equivalent is True

    def test_degrades_to_abstain_on_client_error(self):
        judge = LLMJudge(_RaisingClient())
        verdict = judge.is_equivalent("drug", "a", "b")
        assert verdict.equivalent is None
        assert "error" in verdict.rationale.lower()

    def test_degrades_on_invalid_response(self):
        class _BadClient(LLMJudgeClient):
            def judge(self, field, predicted, ground_truth):  # type: ignore[override]
                return "not a verdict"  # type: ignore[return-value]

        judge = LLMJudge(_BadClient())
        verdict = judge.is_equivalent("drug", "a", "b")
        assert verdict.equivalent is None


class TestJudgeInHarness:
    def test_equivalent_verdict_turns_mismatch_into_match(self):
        judge = LLMJudge(_StubClient(JudgeVerdict(equivalent=True)))
        preds = [_pred("p1", drug="amoxicilina", dose="500 mg",
                        frequency="c/8h", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]

        without = evaluate(preds, gt)
        assert without.metrics_by_field["frequency"].hallucinations == 1

        with_judge = evaluate(preds, gt, judge=judge)
        freq_m = with_judge.metrics_by_field["frequency"]
        assert freq_m.hallucinations == 0
        assert freq_m.exact == 1

    def test_not_equivalent_keeps_mismatch(self):
        judge = LLMJudge(_StubClient(JudgeVerdict(equivalent=False)))
        preds = [_pred("p1", drug="ibuprofeno", dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        result = evaluate(preds, gt, judge=judge)
        assert result.metrics_by_field["drug"].hallucinations == 1

    def test_judge_not_called_on_abstention(self):
        client = _StubClient(JudgeVerdict(equivalent=True))
        judge = LLMJudge(client)
        preds = [_pred("p1", drug=None, dose="500 mg",
                        frequency="cada 8 horas", duration="7 días", route="oral")]
        gt = [_gt("p1", drug="amoxicilina", dose="500 mg",
                   frequency="cada 8 horas", duration="7 días", route="oral")]
        evaluate(preds, gt, judge=judge)
        assert all(call[0] != "drug" for call in client.calls)


def test_judge_verdict_abstain_factory():
    v = JudgeVerdict.abstain()
    assert v.equivalent is None
