"""Métricas de evaluación por campo para el pipeline de extracción.

Las métricas se reportan siempre POR CAMPO, nunca agregadas a un número único.
Campos evaluados: farmaco, dosis, frecuencia, duracion, via.

Métricas principales:
- exact_match: valor extraído == ground truth (normalizado)
- abstention_rate: fracción de campos marcados ilegible/dudoso
- hallucination_rate: fracción de extracciones incorrectas donde el sistema
  no se abstuvo (el error más costoso según abstencion-obligatoria)
- precision: TP / (TP + FP) sobre los campos donde el sistema dio respuesta
- recall: TP / (TP + FN) sobre todos los campos del ground truth
"""

from dataclasses import dataclass, field

from src.domain.value_objects.campo_extraido import EstadoCampo

CAMPOS_EVALUADOS = ("farmaco", "dosis", "frecuencia", "duracion", "via")


@dataclass
class MetricasCampo:
    campo: str
    total: int = 0
    exactos: int = 0
    abstraidos: int = 0
    alucinaciones: int = 0  # extrajo un valor incorrecto sin abstenerse

    @property
    def exact_match(self) -> float:
        respondidos = self.total - self.abstraidos
        return self.exactos / respondidos if respondidos > 0 else 0.0

    @property
    def abstention_rate(self) -> float:
        return self.abstraidos / self.total if self.total > 0 else 0.0

    @property
    def hallucination_rate(self) -> float:
        respondidos = self.total - self.abstraidos
        return self.alucinaciones / respondidos if respondidos > 0 else 0.0

    @property
    def precision(self) -> float:
        respondidos = self.total - self.abstraidos
        if respondidos == 0:
            return 1.0
        return self.exactos / respondidos

    @property
    def recall(self) -> float:
        return self.exactos / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "campo": self.campo,
            "total": self.total,
            "exact_match": round(self.exact_match, 4),
            "abstention_rate": round(self.abstention_rate, 4),
            "hallucination_rate": round(self.hallucination_rate, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
        }


@dataclass
class ResultadoEval:
    metricas_por_campo: dict[str, MetricasCampo] = field(default_factory=dict)

    def resumen(self) -> list[dict]:
        return [m.to_dict() for m in self.metricas_por_campo.values()]

    def hallucination_rate_total(self) -> float:
        total_respondidos = sum(
            m.total - m.abstraidos for m in self.metricas_por_campo.values()
        )
        total_alucinaciones = sum(m.alucinaciones for m in self.metricas_por_campo.values())
        return total_alucinaciones / total_respondidos if total_respondidos > 0 else 0.0


def _normalizar(valor: str | None) -> str:
    if valor is None:
        return ""
    return valor.lower().strip()


def calcular_metricas(
    predicciones: list[dict],
    ground_truth: list[dict],
) -> ResultadoEval:
    """Calcula métricas por campo comparando predicciones contra ground truth.

    Args:
        predicciones: lista de dicts con campos {receta_id, farmaco, dosis, ...}
                      donde cada valor es un CampoExtraido serializado o None.
        ground_truth: lista de dicts con los mismos campos pero con el valor correcto
                      como string (o None si ese campo no aplica en esa receta).
    """
    resultado = ResultadoEval(
        metricas_por_campo={c: MetricasCampo(campo=c) for c in CAMPOS_EVALUADOS}
    )

    gt_index: dict[str, dict] = {gt["receta_id"]: gt for gt in ground_truth}

    for pred in predicciones:
        receta_id = pred.get("receta_id", "")
        gt = gt_index.get(receta_id)
        if gt is None:
            continue

        for campo in CAMPOS_EVALUADOS:
            metrica = resultado.metricas_por_campo[campo]
            metrica.total += 1

            pred_campo = pred.get(campo)
            gt_valor = gt.get(campo)

            if gt_valor is None:
                metrica.total -= 1
                continue

            if pred_campo is None or pred_campo.get("status") in (
                EstadoCampo.ilegible,
                EstadoCampo.dudoso,
            ):
                metrica.abstraidos += 1
                continue

            pred_valor = _normalizar(pred_campo.get("value"))
            gt_normalizado = _normalizar(gt_valor)

            if pred_valor == gt_normalizado:
                metrica.exactos += 1
            else:
                metrica.alucinaciones += 1

    return resultado
