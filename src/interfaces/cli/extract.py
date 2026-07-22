import asyncio
import hashlib
import sys
from pathlib import Path

from src.interfaces.api.bootstrap import build_extract_uc_standalone as build_extract_uc


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def _run(image_path: Path, print_json: bool) -> None:
    image_bytes = image_path.read_bytes()
    use_case = build_extract_uc()
    prescription = await use_case.execute(image_bytes, _hash(image_bytes))

    if print_json:
        print(prescription.model_dump_json(indent=2))
        return

    print(f"ID:     {prescription.id}")
    print(f"Estado: {prescription.status}")
    print(f"Medicamentos encontrados: {len(prescription.medications)}")
    for i, med in enumerate(prescription.medications, 1):
        print(f"\n  [{i}] Fármaco:    {med.drug.value!r}  ({med.drug.status}, conf={med.drug.confidence:.2f})")
        print(f"      Dosis:      {med.dose.value!r}  ({med.dose.status}, conf={med.dose.confidence:.2f})")
        print(f"      Frecuencia: {med.frequency.value!r}  ({med.frequency.status})")
        print(f"      Duración:   {med.duration.value!r}  ({med.duration.status})")
        print(f"      Vía:        {med.route.value!r}  ({med.route.status})")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extrae medicamentos de una receta médica.")
    parser.add_argument("image", type=Path, help="Ruta a la imagen de la receta")
    parser.add_argument("--print", dest="print_json", action="store_true", help="Salida JSON completa")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"Error: no se encuentra el archivo '{args.image}'", file=sys.stderr)
        sys.exit(1)

    asyncio.run(_run(args.image, args.print_json))


if __name__ == "__main__":
    main()
