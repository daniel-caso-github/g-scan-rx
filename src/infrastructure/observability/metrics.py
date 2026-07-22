from prometheus_client import Counter

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
