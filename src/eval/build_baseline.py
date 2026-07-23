"""Builds src/eval/baseline.json from MEASURED metrics on the seed golden set.

The baseline is the regression floor: a prompt/model change that drops a metric
below these thresholds turns CI red (eval-primero). Thresholds are derived from
the current measurement with a small margin, NOT set arbitrarily.

Margins:
- hallucination_rate_max     = measured + 0.05 (never below a 0.05 floor)
- incorrect_abstention_rate  = measured + 0.10 (abstention is noisier)
- exact_match_min per field  = max(measured - 0.10, 0.0)

Regenerate after regenerating the seed set:
    docker compose run --rm app python -m src.eval.build_baseline
"""

import json
from pathlib import Path

from src.eval.harness import BASELINE_PATH, load_golden_set
from src.eval.metrics import EVALUATED_FIELDS, calculate_metrics


def build_baseline() -> dict:
    predictions, ground_truth = load_golden_set()
    if not predictions or not ground_truth:
        raise RuntimeError(
            "Golden set vacío. Corré `python -m src.eval.seed_golden_set` primero."
        )

    result = calculate_metrics(predictions, ground_truth)

    hr = result.total_hallucination_rate()
    iar = result.total_incorrect_abstention_rate()

    baseline: dict = {
        "_note": (
            "Umbrales MEDIDOS sobre el seed golden set sintético. Regenerar con "
            "python -m src.eval.build_baseline tras cambiar el seed set."
        ),
        "hallucination_rate_max": round(min(hr + 0.05, 1.0), 4),
        "incorrect_abstention_rate_max": round(min(iar + 0.10, 1.0), 4),
        "by_field": {},
    }

    for f in EVALUATED_FIELDS:
        m = result.metrics_by_field[f]
        baseline["by_field"][f] = {
            "exact_match_min": round(max(m.exact_match - 0.10, 0.0), 4),
            "incorrect_abstention_rate_max": round(
                min(m.incorrect_abstention_rate + 0.10, 1.0), 4
            ),
        }

    return baseline


def main() -> None:
    baseline = build_baseline()
    with Path(BASELINE_PATH).open("w") as fh:
        json.dump(baseline, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"baseline.json escrito en {BASELINE_PATH}")


if __name__ == "__main__":
    main()
