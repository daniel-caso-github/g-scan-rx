"""Tests del generador sintético v1."""

from src.domain.entities.receta import EstadoReceta
from src.domain.value_objects.campo_extraido import EstadoCampo


class TestRecetaGenerator:
    def test_genera_recetas(self, generator):
        recetas = generator.generate(n=5)
        assert len(recetas) == 5

    def test_receta_tiene_medicamentos(self, generator):
        recetas = generator.generate(n=3)
        for receta in recetas:
            assert len(receta.medicamentos) >= 1

    def test_campos_tienen_crop(self, generator):
        recetas = generator.generate(n=3)
        for receta in recetas:
            for med in receta.medicamentos:
                for campo in (med.farmaco, med.dosis, med.frecuencia, med.duracion, med.via):
                    assert campo.source_crop is not None

    def test_ilegible_tiene_value_none(self, generator):
        recetas = generator.generate(n=50)
        for receta in recetas:
            for med in receta.medicamentos:
                for campo in (med.farmaco, med.dosis, med.frecuencia, med.duracion, med.via):
                    if campo.status == EstadoCampo.ilegible:
                        assert campo.value is None

    def test_receta_status_pendiente(self, generator):
        receta = generator.generate(n=1)[0]
        assert receta.status == EstadoReceta.pendiente

    def test_ids_deterministas_con_mismo_seed(self, catalog):
        from src.data.synthetic.generator import RecetaGenerator

        gen1 = RecetaGenerator(catalog=catalog, seed=99)
        gen2 = RecetaGenerator(catalog=catalog, seed=99)
        r1 = gen1.generate(n=3)
        r2 = gen2.generate(n=3)
        assert [r.id for r in r1] == [r.id for r in r2]

    def test_ground_truth_tiene_receta_id(self, generator):
        recetas = generator.generate(n=3)
        gt = generator.generate_ground_truth(recetas)
        ids_recetas = {r.id for r in recetas}
        for entry in gt:
            assert entry["receta_id"] in ids_recetas
