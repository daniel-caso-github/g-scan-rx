"""Tests de regresión del harness de evaluación.

Verifican que las métricas se calculan correctamente y que los invariantes
de abstención se mantienen. En CI, una subida de hallucination_rate sobre
el umbral baseline hace fallar el test.
"""

import pytest

from src.domain.value_objects.campo_extraido import EstadoCampo
from src.eval.harness import assert_sin_regresion, evaluar
from src.eval.metrics import CAMPOS_EVALUADOS, calcular_metricas


def _pred(receta_id: str, **campos) -> dict:
    """Helper: construye una predicción serializada."""
    resultado = {"receta_id": receta_id}
    for campo in CAMPOS_EVALUADOS:
        valor = campos.get(campo)
        if valor is None:
            resultado[campo] = {"status": EstadoCampo.ilegible, "value": None}
        elif valor == "__dudoso__":
            resultado[campo] = {"status": EstadoCampo.dudoso, "value": None}
        else:
            resultado[campo] = {"status": EstadoCampo.legible, "value": valor}
    return resultado


def _gt(receta_id: str, **campos) -> dict:
    return {"receta_id": receta_id, **campos}


class TestCalcularMetricas:
    def test_todo_correcto(self):
        preds = [_pred("r1", farmaco="amoxicilina", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = calcular_metricas(preds, gt)
        for campo in CAMPOS_EVALUADOS:
            m = resultado.metricas_por_campo[campo]
            assert m.exact_match == 1.0
            assert m.hallucination_rate == 0.0

    def test_abstenciones_no_cuentan_como_alucinacion(self):
        preds = [_pred("r1", farmaco=None, dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = calcular_metricas(preds, gt)
        farmaco_m = resultado.metricas_por_campo["farmaco"]
        assert farmaco_m.abstraidos == 1
        assert farmaco_m.alucinaciones == 0
        assert farmaco_m.hallucination_rate == 0.0

    def test_valor_incorrecto_cuenta_como_alucinacion(self):
        preds = [_pred("r1", farmaco="ibuprofeno", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = calcular_metricas(preds, gt)
        farmaco_m = resultado.metricas_por_campo["farmaco"]
        assert farmaco_m.alucinaciones == 1
        assert farmaco_m.hallucination_rate == 1.0

    def test_multiple_recetas(self):
        preds = [
            _pred("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral"),
            _pred("r2", farmaco="ibuprofeno", dosis="400 mg",
                   frecuencia="cada 12 horas", duracion="5 días", via="oral"),
        ]
        gt = [
            _gt("r1", farmaco="amoxicilina", dosis="500 mg",
                 frecuencia="cada 8 horas", duracion="7 días", via="oral"),
            _gt("r2", farmaco="ibuprofeno", dosis="400 mg",
                 frecuencia="cada 12 horas", duracion="5 días", via="oral"),
        ]
        resultado = calcular_metricas(preds, gt)
        for campo in CAMPOS_EVALUADOS:
            m = resultado.metricas_por_campo[campo]
            assert m.total == 2
            assert m.exactos == 2

    def test_dudoso_cuenta_como_abstencion(self):
        preds = [_pred("r1", farmaco="__dudoso__", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = calcular_metricas(preds, gt)
        farmaco_m = resultado.metricas_por_campo["farmaco"]
        assert farmaco_m.abstraidos == 1
        assert farmaco_m.alucinaciones == 0

    def test_hallucination_rate_total(self):
        preds = [_pred("r1", farmaco="ibuprofeno", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = calcular_metricas(preds, gt)
        hr = resultado.hallucination_rate_total()
        assert hr > 0.0


class TestAssertSinRegresion:
    def test_pasa_bajo_umbral(self):
        preds = [_pred("r1", farmaco="amoxicilina", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = evaluar(preds, gt)
        assert_sin_regresion(resultado, {"hallucination_rate_max": 0.05})

    def test_falla_sobre_umbral(self):
        preds = [_pred("r1", farmaco="ibuprofeno", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = evaluar(preds, gt)
        with pytest.raises(AssertionError, match="Regresión detectada"):
            assert_sin_regresion(resultado, {"hallucination_rate_max": 0.05})

    def test_falla_por_exact_match_bajo(self):
        preds = [_pred("r1", farmaco="ibuprofeno", dosis="500 mg",
                        frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        gt = [_gt("r1", farmaco="amoxicilina", dosis="500 mg",
                   frecuencia="cada 8 horas", duracion="7 días", via="oral")]
        resultado = evaluar(preds, gt)
        with pytest.raises(AssertionError, match="Regresión en campo 'farmaco'"):
            assert_sin_regresion(
                resultado,
                {"hallucination_rate_max": 1.0, "por_campo": {"farmaco": {"exact_match_min": 0.9}}},
            )
