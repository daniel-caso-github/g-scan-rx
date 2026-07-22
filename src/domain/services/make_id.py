import hashlib


def make_id(*parts: str) -> str:
    """ID determinista a partir de uno o más strings.

    Idempotente: mismos inputs → mismo ID. Usado para entidades y catálogo.
    """
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:24]
