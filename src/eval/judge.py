"""LLM-as-judge for ambiguous eval cases.

The automatic metrics in `metrics.py` decide most cases by normalized exact
match. Some cases are genuinely ambiguous: the prediction and the ground truth
differ as strings but may be semantically equivalent (synonyms, abbreviations,
formatting), e.g. "cada 8 horas" vs "c/8h", "vía oral" vs "oral", "500mg" vs
"500 mg". For those the judge is consulted to break the tie.

Design (follows the project's port + fail-contract convention):
- `LLMJudgeClient` is a port (ABC). The concrete client is injected; the eval
  layer never talks to a network directly and tests mock this port.
- `LLMJudge` degrades on any client failure to an ABSTAIN verdict
  (`equivalent=None`) so a broken judge never crashes the harness and never
  silently marks a mismatch as a match. Ambiguous-and-unjudged falls back to
  the strict string comparison (i.e. counts as a mismatch).

Judging criterion (documented, deterministic prompt):
- The judge answers ONLY whether the predicted value and the ground-truth value
  refer to the SAME clinical fact for the given field. Synonyms, standard
  abbreviations, unit spacing and ordering count as equivalent. A different
  drug, a different dose magnitude, or a different unit do NOT.
- The judge NEVER invents a value; it only compares the two given strings.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    """Result of a single judged comparison.

    equivalent:
        True  -> the two values mean the same clinical fact (count as match)
        False -> they differ (count as mismatch)
        None  -> the judge abstained / was unavailable (fail-contract: the
                 caller falls back to strict string comparison)
    """

    equivalent: bool | None
    rationale: str = ""

    model_config = {"frozen": True}

    @classmethod
    def abstain(cls, rationale: str = "judge unavailable") -> "JudgeVerdict":
        return cls(equivalent=None, rationale=rationale)


class LLMJudgeClient(ABC):
    """Port: single-call client that judges semantic equivalence of two values.

    Concrete implementations wrap an LLM. They MAY raise; `LLMJudge` catches and
    degrades. Implementations must not invent values, only compare the two.
    """

    @abstractmethod
    def judge(self, field: str, predicted: str, ground_truth: str) -> JudgeVerdict:
        ...


JUDGE_SYSTEM_PROMPT = (
    "Eres un evaluador clínico. Recibes el nombre de un campo de una receta "
    "(drug, dose, frequency, duration o route) y dos valores de texto: el "
    "predicho por el sistema y el de referencia (ground truth). Responde ÚNICA "
    "y exclusivamente si ambos valores describen el MISMO hecho clínico para ese "
    "campo. Sinónimos, abreviaturas estándar, espaciado de unidades y orden de "
    "palabras cuentan como equivalentes. Un fármaco distinto, una magnitud de "
    "dosis distinta o una unidad distinta NO son equivalentes. Nunca inventes un "
    "valor: solo compara los dos textos dados."
)


class LLMJudge:
    """Wraps an `LLMJudgeClient` with the project fail-contract.

    Only invoked for cases the automatic metric flags as ambiguous.
    """

    def __init__(self, client: LLMJudgeClient) -> None:
        self._client = client

    def is_equivalent(self, field: str, predicted: str, ground_truth: str) -> JudgeVerdict:
        try:
            verdict = self._client.judge(field, predicted, ground_truth)
        except Exception as exc:  # noqa: BLE001 — fail-contract: never raise upward
            return JudgeVerdict.abstain(f"error del juez: {exc}")
        if not isinstance(verdict, JudgeVerdict):
            return JudgeVerdict.abstain("respuesta del juez con formato inválido")
        return verdict
