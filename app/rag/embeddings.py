"""Local embedding model wrapper (sentence-transformers)."""

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from app.config import settings


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("query text is empty")
    return embed_texts([cleaned])[0]
