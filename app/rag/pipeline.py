"""End-to-end RAG pipeline."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.rag.embeddings import embed_query
from app.rag.generate import generate_answer
from app.rag.ingest import ensure_index, ingest_knowledge_base, ingest_paths
from app.rag.store import RetrievedChunk, VectorStore


class RAGPipeline:
    def __init__(self) -> None:
        self.store = VectorStore()

    def ensure_ready(self) -> dict:
        return ensure_index(self.store)

    def reindex(self) -> dict:
        return ingest_knowledge_base(self.store, clear=True)

    def ingest_file(self, path: Path) -> dict:
        return ingest_paths([path], store=self.store)

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        embedding = embed_query(question)
        return self.store.query(embedding, top_k=top_k or settings.top_k)

    def ask(self, question: str, top_k: int | None = None) -> dict:
        cleaned = (question or "").strip()
        if not cleaned:
            raise ValueError("question is empty")
        self.ensure_ready()
        chunks = self.retrieve(cleaned, top_k=top_k)
        result = generate_answer(cleaned, chunks)
        result["top_k"] = top_k or settings.top_k
        result["chunk_count"] = self.store.count()
        return result

    def health(self) -> dict:
        return {
            "chunks": self.store.count(),
            "knowledge_base": str(settings.knowledge_base_dir),
            "chroma_dir": str(settings.chroma_dir),
            "embedding_model": settings.embedding_model,
            "llm": (
                f"openai:{settings.openai_model}"
                if settings.use_openai
                else f"ollama:{settings.ollama_model}"
            ),
        }
