from prometheus_client import Counter

from src.domain.entities.verified_record import VerifiedRecord

ABSTENTIONS_TOTAL = Counter(
    "gscan_abstentions_total",
    "Agent abstentions due to out-of-distribution images",
)
EXTRACTIONS_TOTAL = Counter(
    "gscan_extractions_total",
    "Total prescription extraction attempts",
    ["result"],
)
TOKENS_TOTAL = Counter(
    "gscan_tokens_total",
    "Total LLM tokens consumed",
    ["model", "direction"],
)
COST_USD_TOTAL = Counter(
    "gscan_cost_usd_total",
    "Estimated LLM cost in USD",
    ["model"],
)
CACHE_HITS_TOTAL = Counter(
    "gscan_cache_hits_total",
    "Semantic cache hits (extraction skipped)",
)
CIRCUIT_OPEN_TOTAL = Counter(
    "gscan_circuit_open_total",
    "Requests rejected by an open circuit breaker",
    ["service"],
)
VERDICT_STATUS_TOTAL = Counter(
    "gscan_verdicts_total",
    "Drug verification verdicts against the catalog (not_found is a hallucination proxy)",
    ["status"],
)


def record_verdicts(record: VerifiedRecord) -> None:
    """Records the drug verdict per medication; not_found is the hallucination proxy."""
    for med in record.medications:
        VERDICT_STATUS_TOTAL.labels(status=med.drug.verdict.status).inc()
