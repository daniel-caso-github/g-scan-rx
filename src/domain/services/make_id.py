import hashlib


def make_id(*parts: str) -> str:
    """Deterministic ID from one or more strings.

    Idempotent: same inputs → same ID. Used for entities and catalog items.
    """
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:24]
