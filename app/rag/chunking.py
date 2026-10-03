"""Text chunking helpers for RAG ingest."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: str
    index: int


def split_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    """Split text into overlapping character windows, preferring paragraph breaks."""
    cleaned = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))
    cleaned = cleaned.strip()
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        overlap = 0
    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    n = len(cleaned)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            window = cleaned[start:end]
            # Prefer break at paragraph, then sentence, then space
            break_at = max(window.rfind("\n\n"), window.rfind(". "), window.rfind(" "))
            if break_at > chunk_size // 3:
                end = start + break_at + 1
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        next_start = end - overlap
        # Overlap must not stall the window, or a large overlap loops forever.
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def make_chunks(
    text: str,
    source: str,
    chunk_size: int = 700,
    overlap: int = 120,
) -> list[Chunk]:
    parts = split_text(text, chunk_size=chunk_size, overlap=overlap)
    return [
        Chunk(
            text=part,
            source=source,
            chunk_id=f"{source}::chunk-{i}",
            index=i,
        )
        for i, part in enumerate(parts)
    ]
