from __future__ import annotations

from src.domain.entities.catalog_item import CatalogItem


class Embedder:
    """sentence-transformers wrapper with lazy loading."""

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    @staticmethod
    def text_for_item(item: CatalogItem) -> str:
        parts = [item.active_ingredient]
        if item.brand_name:
            parts.append(item.brand_name)
        parts.append(item.presentation)
        return " ".join(parts).strip()
