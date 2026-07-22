import pytest

from src.domain.value_objects.campo_extraido import CampoExtraido, EstadoCampo
from src.domain.value_objects.dosis_normalizada import DosisNormalizada
from src.domain.value_objects.recorte_imagen import RecorteImagen
from src.domain.value_objects.veredicto_verificacion import EstadoVeredicto, VeredictoVerificacion


class TestRecorteImagen:
    def test_crea_correctamente(self):
        r = RecorteImagen(bbox=(10, 20, 100, 30), crop_ref="test.png")
        assert r.bbox == (10, 20, 100, 30)

    def test_rechaza_ancho_cero(self):
        with pytest.raises(ValueError):
            RecorteImagen(bbox=(0, 0, 0, 30), crop_ref="x.png")

    def test_rechaza_coordenadas_negativas(self):
        with pytest.raises(ValueError):
            RecorteImagen(bbox=(-1, 0, 100, 30), crop_ref="x.png")

    def test_inmutable(self, recorte_dummy):
        with pytest.raises((TypeError, ValueError)):
            recorte_dummy.crop_ref = "otro.png"


class TestCampoExtraido:
    def test_campo_legible(self, recorte_dummy):
        c = CampoExtraido(
            value="amoxicilina",
            confidence=0.9,
            status=EstadoCampo.legible,
            source_crop=recorte_dummy,
        )
        assert c.value == "amoxicilina"
        assert c.status == EstadoCampo.legible

    def test_ilegible_requiere_value_none(self, recorte_dummy):
        with pytest.raises(ValueError):
            CampoExtraido(
                value="algo",
                confidence=0.2,
                status=EstadoCampo.ilegible,
                source_crop=recorte_dummy,
            )

    def test_legible_requiere_value(self, recorte_dummy):
        with pytest.raises(ValueError):
            CampoExtraido(
                value=None,
                confidence=0.9,
                status=EstadoCampo.legible,
                source_crop=recorte_dummy,
            )

    def test_confidence_fuera_de_rango(self, recorte_dummy):
        with pytest.raises(ValueError):
            CampoExtraido(
                value="x",
                confidence=1.5,
                status=EstadoCampo.legible,
                source_crop=recorte_dummy,
            )

    def test_campo_ilegible_correcto(self, recorte_dummy):
        c = CampoExtraido(
            value=None,
            confidence=0.1,
            status=EstadoCampo.ilegible,
            source_crop=recorte_dummy,
        )
        assert c.value is None


class TestDosisNormalizada:
    def test_crea_correctamente(self):
        d = DosisNormalizada(amount=500.0, unit="mg", frequency_hours=8.0, route="oral")
        assert d.amount == 500.0
        assert d.unit == "mg"

    def test_amount_negativo_rechazado(self):
        with pytest.raises(ValueError):
            DosisNormalizada(amount=-10.0, unit="mg")

    def test_unidad_no_canonica_rechazada(self):
        with pytest.raises(ValueError):
            DosisNormalizada(amount=500.0, unit="kilogramos")

    def test_via_no_canonica_rechazada(self):
        with pytest.raises(ValueError):
            DosisNormalizada(amount=500.0, unit="mg", route="intragástrica")

    def test_campos_opcionales_none(self):
        d = DosisNormalizada(amount=20.0, unit="mg")
        assert d.frequency_hours is None
        assert d.route is None


class TestVeredictoVerificacion:
    def test_verificado_requiere_catalog_id(self):
        with pytest.raises(ValueError):
            VeredictoVerificacion(
                status=EstadoVeredicto.verificado,
                catalog_item_id=None,
                match_score=0.95,
            )

    def test_dudoso_sin_catalog_id(self):
        v = VeredictoVerificacion(status=EstadoVeredicto.dudoso, match_score=0.4)
        assert v.catalog_item_id is None

    def test_no_disponible(self):
        v = VeredictoVerificacion.no_disponible()
        assert v.status == EstadoVeredicto.dudoso
        assert "verificación no disponible" in v.notes

    def test_match_score_fuera_de_rango(self):
        with pytest.raises(ValueError):
            VeredictoVerificacion(status=EstadoVeredicto.dudoso, match_score=1.5)
