"""Builds the SEED golden set (synthetic, fictional) for the eval harness.

This is NOT the full golden set. It bootstraps the harness so metrics, the
baseline and the regression gate can run today. The real golden set
(100-200 handwritten fictional prescriptions annotated field by field) is
filled in by hand later — see tests/fixtures/golden_set/README.md.

What it produces (offline, deterministic with a fixed seed):
- predictions.jsonl : one row per prescription, each field a serialized
  ExtractedField {value, confidence, status, source_crop}.
- ground_truth.jsonl : one row per prescription with the correct string per
  field plus an "unreadable" map {field: bool} marking the fields that are
  GENUINELY illegible in the source (abstencion-calibrada). A field marked
  unreadable has its value set to None.

Rules honored:
- cero-datos-reales: all data comes from the synthetic generator / seed catalog.
- abstencion-calibrada: unreadable ground-truth fields are labeled so that
  abstaining on them counts as a CORRECT abstention.

Regenerate with:
    docker compose run --rm app python -m src.eval.seed_golden_set --n 12
"""

import argparse
import json
from pathlib import Path
from typing import Any

from src.data.synthetic.catalog_seed import get_seed_catalog
from src.data.synthetic.generator import PrescriptionGenerator
from src.domain.entities.prescription import Prescription
from src.domain.value_objects.extracted_field import ExtractedField, FieldStatus

EVALUATED_FIELDS = ("drug", "dose", "frequency", "duration", "route")
DEFAULT_OUTPUT_DIR = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "golden_set"
)
DEFAULT_SEED = 20260722
DEFAULT_N = 12


def _serialize_field(field: ExtractedField) -> dict[str, Any]:
    return {
        "value": field.value,
        "confidence": round(field.confidence, 4),
        "status": field.status.value,
        "source_crop": {
            "bbox": list(field.source_crop.bbox),
            "crop_ref": field.source_crop.crop_ref,
        },
    }


def build_rows(
    prescriptions: list[Prescription],
) -> tuple[list[dict], list[dict]]:
    """Turns synthetic prescriptions into (predictions, ground_truth) rows.

    Ground-truth policy for the seed set:
    - readable field  -> gt value = the generated value, unreadable=False.
    - uncertain field -> treated as a legible field the system was unsure about
      (gt keeps the intended value, unreadable=False). The system abstained, so
      this is an INCORRECT abstention in the metrics — realistic signal.
    - unreadable field-> gt value = None, unreadable=True. Abstaining is CORRECT.
    """
    predictions: list[dict] = []
    ground_truth: list[dict] = []

    for prescription in prescriptions:
        med = prescription.medications[0]
        fields = {
            "drug": med.drug,
            "dose": med.dose,
            "frequency": med.frequency,
            "duration": med.duration,
            "route": med.route,
        }

        pred_row: dict[str, Any] = {"prescription_id": prescription.id}
        gt_row: dict[str, Any] = {"prescription_id": prescription.id}
        unreadable_map: dict[str, bool] = {}

        for name in EVALUATED_FIELDS:
            field = fields[name]
            pred_row[name] = _serialize_field(field)

            if field.status == FieldStatus.unreadable:
                gt_row[name] = None
                unreadable_map[name] = True
            elif field.status == FieldStatus.uncertain:
                # Ground truth is the intended (legible) value; the system was
                # unsure. Recover it from the degraded/intended value if present.
                gt_row[name] = field.value
                unreadable_map[name] = False
            else:
                gt_row[name] = field.value
                unreadable_map[name] = False

        gt_row["unreadable"] = unreadable_map
        predictions.append(pred_row)
        ground_truth.append(gt_row)

    return predictions, ground_truth


def _write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False))
            f.write("\n")


def generate_seed_set(
    n: int = DEFAULT_N,
    seed: int = DEFAULT_SEED,
    output_dir: Path | None = None,
) -> tuple[list[dict], list[dict]]:
    catalog = get_seed_catalog()
    generator = PrescriptionGenerator(catalog=catalog, seed=seed)
    prescriptions = generator.generate(n=n)
    predictions, ground_truth = build_rows(prescriptions)

    directory = output_dir or DEFAULT_OUTPUT_DIR
    _write_jsonl(predictions, directory / "predictions.jsonl")
    _write_jsonl(ground_truth, directory / "ground_truth.jsonl")
    return predictions, ground_truth


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el seed golden set sintético.")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    preds, gt = generate_seed_set(n=args.n, seed=args.seed, output_dir=args.output_dir)
    unreadable = sum(
        1 for row in gt for f in EVALUATED_FIELDS if (row.get("unreadable") or {}).get(f)
    )
    print(
        f"Seed golden set generado: {len(preds)} recetas, "
        f"{unreadable} campos marcados ilegibles."
    )


if __name__ == "__main__":
    main()
