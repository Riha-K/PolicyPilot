"""ChromaDB vector store helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


@dataclass
class RetrievedChunk:
    text: str
    source: str
    chunk_id: str
    score: float


class VectorStore:
    def __init__(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self.collection.count())

    def clear(self) -> None:
        name = settings.collection_name
        try:
            self.client.delete_collection(name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not ids:
            return
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(self, embedding: list[float], top_k: int | None = None) -> list[RetrievedChunk]:
        k = top_k or settings.top_k
        if self.count() == 0:
            return []
        k = min(k, self.count())
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]

        out: list[RetrievedChunk] = []
        for doc, meta, dist, cid in zip(docs, metas, dists, ids):
            # cosine distance -> similarity-ish score
            score = 1.0 - float(dist) if dist is not None else 0.0
            out.append(
                RetrievedChunk(
                    text=doc or "",
                    source=str((meta or {}).get("source", "unknown")),
                    chunk_id=str(cid),
                    score=score,
                )
            )
        return out
