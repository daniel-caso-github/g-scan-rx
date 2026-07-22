"""Generador sintético v1 de recetas médicas ficticias.

Genera instancias de MedicamentoExtraido y Receta a partir del catálogo seed.
Produce texto plausible con confianzas variables para simular errores de lectura.

Uso:
    from src.data.synthetic.generator import RecetaGenerator
    from src.data.synthetic.catalog_seed import get_seed_catalog

    gen = RecetaGenerator(catalog=get_seed_catalog(), seed=42)
    recetas = gen.generate(n=10)
"""

import hashlib
import random
from typing import Any

from src.domain.entities.item_catalogo import ItemCatalogo
from src.domain.entities.medicamento_extraido import MedicamentoExtraido
from src.domain.entities.receta import EstadoReceta, Receta
from src.domain.services.make_id import make_id
from src.domain.value_objects.campo_extraido import CampoExtraido, EstadoCampo
from src.domain.value_objects.recorte_imagen import RecorteImagen

_FRECUENCIAS = [
    "cada 8 horas",
    "cada 12 horas",
    "cada 24 horas",
    "dos veces al día",
    "tres veces al día",
    "una vez al día",
]

_DURACIONES = [
    "5 días",
    "7 días",
    "10 días",
    "14 días",
    "1 mes",
    "2 semanas",
]

_VIAS = ["oral", "tópica", "inhalatoria", "sublingual"]

_DEGRADACIONES = {
    "tipográficos": {
        "amoxicilina": ["amoxicilína", "amoxicilin", "amoxiciIina"],
        "ibuprofeno": ["ibuprofebo", "ibuprofen", "ibuprofeno"],
        "paracetamol": ["paracetanol", "paracetamol", "paracetmol"],
        "omeprazol": ["omeprazole", "omeprazol", "omeprazole"],
        "metformina": ["metfornina", "metformína", "metfomina"],
        "atorvastatina": ["atorvastatína", "atorvastina", "atrovastatina"],
        "losartan": ["lozartan", "losartan", "losartán"],
        "azitromicina": ["azitromicína", "azitromicina", "azitromiicna"],
    }
}


class RecetaGenerator:
    """Genera recetas sintéticas ficticias a partir de un catálogo seed."""

    def __init__(self, catalog: list[ItemCatalogo], seed: int = 0) -> None:
        self.catalog = catalog
        self._rng = random.Random(seed)

    def generate(self, n: int = 1) -> list[Receta]:
        return [self._generar_receta(i) for i in range(n)]

    def generate_medicamentos(self, n: int = 1) -> list[MedicamentoExtraido]:
        return [self._generar_medicamento() for _ in range(n)]

    def _generar_receta(self, idx: int) -> Receta:
        n_medicamentos = self._rng.randint(1, 3)
        medicamentos = [self._generar_medicamento() for _ in range(n_medicamentos)]
        imagen_hash = hashlib.sha256(f"synthetic-{idx}".encode()).hexdigest()
        return Receta(
            id=make_id("synthetic", str(idx)),
            image_hash=imagen_hash,
            medicamentos=medicamentos,
            status=EstadoReceta.pendiente,
        )

    def _generar_medicamento(self) -> MedicamentoExtraido:
        item = self._rng.choice(self.catalog)
        recorte_linea = self._recorte_aleatorio()

        farmaco = self._campo_farmaco(item, recorte_linea)
        dosis = self._campo_dosis(item, self._recorte_aleatorio())
        frecuencia = self._campo_texto(
            self._rng.choice(_FRECUENCIAS), self._recorte_aleatorio()
        )
        duracion = self._campo_texto(
            self._rng.choice(_DURACIONES), self._recorte_aleatorio()
        )
        via = self._campo_texto(self._rng.choice(_VIAS), self._recorte_aleatorio())

        return MedicamentoExtraido(
            farmaco=farmaco,
            dosis=dosis,
            frecuencia=frecuencia,
            duracion=duracion,
            via=via,
            recorte=recorte_linea,
        )

    def _campo_farmaco(self, item: ItemCatalogo, crop: RecorteImagen) -> CampoExtraido:
        r = self._rng.random()
        nombre_base = item.active_ingredient

        if r < 0.05:
            return CampoExtraido(
                value=None,
                confidence=self._rng.uniform(0.0, 0.35),
                status=EstadoCampo.ilegible,
                source_crop=crop,
            )

        if r < 0.20:
            degradados = _DEGRADACIONES["tipográficos"].get(nombre_base, [nombre_base])
            valor = self._rng.choice(degradados)
            return CampoExtraido(
                value=valor,
                confidence=self._rng.uniform(0.40, 0.65),
                status=EstadoCampo.dudoso,
                source_crop=crop,
            )

        return CampoExtraido(
            value=nombre_base,
            confidence=self._rng.uniform(0.75, 1.0),
            status=EstadoCampo.legible,
            source_crop=crop,
        )

    def _campo_dosis(self, item: ItemCatalogo, crop: RecorteImagen) -> CampoExtraido:
        r = self._rng.random()
        concentration = item.concentration or "500 mg"

        if r < 0.05:
            return CampoExtraido(
                value=None,
                confidence=self._rng.uniform(0.0, 0.35),
                status=EstadoCampo.ilegible,
                source_crop=crop,
            )

        if r < 0.15:
            partes = concentration.split()
            if len(partes) >= 2:
                try:
                    num = float(partes[0])
                    valor_erroneo = f"{num * 10:.0f} {partes[1]}"
                except ValueError:
                    valor_erroneo = concentration
            else:
                valor_erroneo = concentration
            return CampoExtraido(
                value=valor_erroneo,
                confidence=self._rng.uniform(0.40, 0.60),
                status=EstadoCampo.dudoso,
                source_crop=crop,
            )

        return CampoExtraido(
            value=concentration,
            confidence=self._rng.uniform(0.75, 1.0),
            status=EstadoCampo.legible,
            source_crop=crop,
        )

    def _campo_texto(self, value: str, crop: RecorteImagen) -> CampoExtraido:
        r = self._rng.random()
        if r < 0.05:
            return CampoExtraido(
                value=None,
                confidence=self._rng.uniform(0.0, 0.35),
                status=EstadoCampo.ilegible,
                source_crop=crop,
            )
        confidence = self._rng.uniform(0.65, 1.0)
        status = EstadoCampo.legible if confidence >= 0.7 else EstadoCampo.dudoso
        return CampoExtraido(
            value=value,
            confidence=confidence,
            status=status,
            source_crop=crop,
        )

    def _recorte_aleatorio(self) -> RecorteImagen:
        x = self._rng.randint(0, 400)
        y = self._rng.randint(0, 600)
        w = self._rng.randint(100, 500)
        h = self._rng.randint(20, 60)
        return RecorteImagen(bbox=(x, y, w, h), crop_ref=f"crop_{x}_{y}_{w}_{h}.png")

    def generate_ground_truth(self, recetas: list[Receta]) -> list[dict[str, Any]]:
        """Genera anotaciones ground-truth a partir de recetas sintéticas conocidas.

        Solo válido para recetas creadas por este mismo generador (el valor correcto
        es conocido porque lo generamos nosotros). Para el golden set real
        (manuscritura humana), las anotaciones se cargan desde tests/fixtures/golden_set/.
        """
        ground_truth = []
        for receta in recetas:
            for med in receta.medicamentos:
                ground_truth.append({
                    "receta_id": receta.id,
                    "farmaco": med.farmaco.value,
                    "dosis": med.dosis.value,
                    "frecuencia": med.frecuencia.value,
                    "duracion": med.duracion.value,
                    "via": med.via.value,
                })
        return ground_truth
