import pytest

from src.domain.entities.ficha_verificada import (
    CampoVerificado,
    FichaVerificada,
    MedicamentoVerificado,
)
from src.domain.entities.item_catalogo import ItemCatalogo
from src.domain.entities.receta import EstadoReceta, Receta
from src.domain.services.make_id import make_id
from src.domain.value_objects.campo_extraido import CampoExtraido, EstadoCampo
from src.domain.value_objects.recorte_imagen import RecorteImagen
from src.domain.value_objects.veredicto_verificacion import EstadoVeredicto, VeredictoVerificacion


@pytest.fixture
def crop():
    return RecorteImagen(bbox=(0, 0, 100, 30), crop_ref="c.png")


@pytest.fixture
def campo_legible(crop):
    return CampoExtraido(value="amoxicilina", confidence=0.9, status=EstadoCampo.legible, source_crop=crop)


@pytest.fixture
def campo_ilegible(crop):
    return CampoExtraido(value=None, confidence=0.1, status=EstadoCampo.ilegible, source_crop=crop)


@pytest.fixture
def veredicto_verificado():
    return VeredictoVerificacion(
        status=EstadoVeredicto.verificado,
        catalog_item_id="abc123",
        match_score=0.95,
    )


@pytest.fixture
def veredicto_dudoso():
    return VeredictoVerificacion(status=EstadoVeredicto.dudoso, match_score=0.3)


@pytest.fixture
def item_catalogo():
    return ItemCatalogo(
        id=make_id("cima", "amoxicilina", "cápsula 500 mg"),
        active_ingredient="amoxicilina",
        brand_name="Amoxil",
        presentation="cápsula 500 mg",
        source="cima",
    )


class TestItemCatalogo:
    def test_source_invalida_rechazada(self):
        with pytest.raises(ValueError):
            ItemCatalogo(
                id="x",
                active_ingredient="x",
                presentation="x",
                source="fda",
            )

    def test_id_vacio_rechazado(self):
        with pytest.raises(ValueError):
            ItemCatalogo(id="  ", active_ingredient="x", presentation="x", source="cima")

    def test_make_id_determinista(self, item_catalogo):
        id1 = make_id("cima", "amoxicilina", "cápsula 500 mg")
        id2 = make_id("cima", "amoxicilina", "cápsula 500 mg")
        assert id1 == id2


class TestReceta:
    def test_receta_vacia(self):
        r = Receta(id="r1", image_hash="abc123")
        assert r.medicamentos == []
        assert r.status == EstadoReceta.pendiente

    def test_receta_inmutable(self):
        r = Receta(id="r1", image_hash="abc")
        with pytest.raises((TypeError, ValueError)):
            r.status = EstadoReceta.confirmada


class TestFichaVerificada:
    def _make_campo_verificado(self, campo, veredicto):
        return CampoVerificado(campo=campo, veredicto=veredicto)

    def _make_medicamento_verificado(self, campo_legible, veredicto_verificado):
        cv = CampoVerificado(campo=campo_legible, veredicto=veredicto_verificado)
        return MedicamentoVerificado(
            farmaco=cv, dosis=cv, frecuencia=cv, duracion=cv, via=cv
        )

    def test_ficha_sin_revision(self, campo_legible, veredicto_verificado):
        med = self._make_medicamento_verificado(campo_legible, veredicto_verificado)
        ficha = FichaVerificada(
            receta_id="r1",
            medicamentos=[med],
            overall_confidence=0.9,
            needs_review=False,
        )
        assert not ficha.needs_review

    def test_ficha_con_campo_ilegible_requiere_revision(
        self, campo_ilegible, campo_legible, veredicto_verificado, veredicto_dudoso
    ):
        cv_ilegible = CampoVerificado(campo=campo_ilegible, veredicto=veredicto_dudoso)
        cv_legible = CampoVerificado(campo=campo_legible, veredicto=veredicto_verificado)
        med = MedicamentoVerificado(
            farmaco=cv_ilegible,
            dosis=cv_legible,
            frecuencia=cv_legible,
            duracion=cv_legible,
            via=cv_legible,
        )
        ficha = FichaVerificada(
            receta_id="r1",
            medicamentos=[med],
            overall_confidence=0.5,
            needs_review=True,
        )
        assert ficha.needs_review

    def test_ficha_inconsistente_rechazada(self, campo_ilegible, campo_legible, veredicto_dudoso, veredicto_verificado):
        cv_ilegible = CampoVerificado(campo=campo_ilegible, veredicto=veredicto_dudoso)
        cv_legible = CampoVerificado(campo=campo_legible, veredicto=veredicto_verificado)
        med = MedicamentoVerificado(
            farmaco=cv_ilegible, dosis=cv_legible, frecuencia=cv_legible,
            duracion=cv_legible, via=cv_legible,
        )
        with pytest.raises(ValueError):
            FichaVerificada(
                receta_id="r1",
                medicamentos=[med],
                overall_confidence=0.5,
                needs_review=False,
            )
