"""Ingest knowledge-base files into the vector store."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.rag.chunking import make_chunks
from app.rag.embeddings import embed_texts
from app.rag.store import VectorStore

SUPPORTED = {".md", ".txt", ".pdf"}


def read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def iter_kb_files(kb_dir: Path | None = None) -> list[Path]:
    root = kb_dir or settings.knowledge_base_dir
    if not root.exists():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            files.append(path)
    return files


def ingest_paths(paths: list[Path], store: VectorStore | None = None) -> dict:
    store = store or VectorStore()
    all_ids: list[str] = []
    all_docs: list[str] = []
    all_meta: list[dict] = []

    for path in paths:
        text = read_file(path)
        rel = str(path.relative_to(settings.root)) if path.is_relative_to(settings.root) else path.name
        chunks = make_chunks(
            text,
            source=rel,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        for chunk in chunks:
            all_ids.append(chunk.chunk_id)
            all_docs.append(chunk.text)
            all_meta.append({"source": chunk.source, "index": chunk.index})

    if not all_docs:
        return {"files": 0, "chunks": 0, "total_in_store": store.count()}

    # Embed in batches to keep memory stable
    batch = 32
    for i in range(0, len(all_docs), batch):
        docs = all_docs[i : i + batch]
        ids = all_ids[i : i + batch]
        metas = all_meta[i : i + batch]
        emb = embed_texts(docs)
        store.upsert(ids=ids, documents=docs, embeddings=emb, metadatas=metas)

    return {
        "files": len(paths),
        "chunks": len(all_docs),
        "total_in_store": store.count(),
    }


def ingest_knowledge_base(store: VectorStore | None = None, clear: bool = False) -> dict:
    store = store or VectorStore()
    if clear:
        store.clear()
    files = iter_kb_files()
    result = ingest_paths(files, store=store)
    result["sources"] = [str(p.relative_to(settings.knowledge_base_dir)) for p in files]
    return result


def ensure_index(store: VectorStore | None = None) -> dict:
    """Ingest knowledge base if the vector store is empty."""
    store = store or VectorStore()
    if store.count() > 0:
        return {"ingested": False, "total_in_store": store.count()}
    result = ingest_knowledge_base(store=store, clear=False)
    result["ingested"] = True
    return result
