"""Central configuration loaded from environment / .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


class Settings:
    root: Path = ROOT
    knowledge_base_dir: Path = Path(
        os.getenv("KNOWLEDGE_BASE_DIR", str(ROOT / "knowledge_base"))
    )
    if not knowledge_base_dir.is_absolute():
        knowledge_base_dir = ROOT / knowledge_base_dir

    chroma_dir: Path = Path(os.getenv("CHROMA_DIR", str(ROOT / "data" / "chroma")))
    if not chroma_dir.is_absolute():
        chroma_dir = ROOT / chroma_dir

    collection_name: str = os.getenv("COLLECTION_NAME", "policy_pilot")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    chunk_size: int = _int("CHUNK_SIZE", 700)
    chunk_overlap: int = _int("CHUNK_OVERLAP", 120)
    top_k: int = _int("TOP_K", 4)

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2").strip()

    @property
    def use_openai(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
