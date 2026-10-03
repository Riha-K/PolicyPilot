"""LLM generation with OpenAI or Ollama backends."""

from __future__ import annotations

import httpx

from app.config import settings
from app.rag.store import RetrievedChunk

SYSTEM_PROMPT = """You are PolicyPilot, a helpful Customer Experience (CX) assistant for an e-commerce company.
Answer ONLY using the provided context snippets from company policies and help articles.
If the answer is not in the context, say you do not have enough information and suggest contacting support.
Be concise, accurate, and polite. Mention relevant policy limits (fees, windows, eligibility) when present.
Do not invent order IDs, fees, or policies that are not in the context.
"""


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        context = "(No retrieved context.)"
    else:
        blocks = []
        for i, c in enumerate(chunks, start=1):
            blocks.append(f"[{i}] Source: {c.source}\n{c.text}")
        context = "\n\n".join(blocks)
    return (
        f"Context:\n{context}\n\n"
        f"Customer question: {question}\n\n"
        "Answer using only the context above."
    )


def _extractive_fallback(question: str, chunks: list[RetrievedChunk]) -> str:
    """Return a useful answer from retrieved text when no LLM is reachable."""
    if not chunks:
        return (
            "No relevant policy chunks were retrieved, and no LLM backend is available. "
            "Add documents to knowledge_base/ or configure OpenAI/Ollama."
        )
    lines = [
        f"**Extractive answer** (LLM unavailable — showing top retrieved policy text for: _{question}_)",
        "",
    ]
    for i, c in enumerate(chunks[:3], start=1):
        lines.append(f"**[{i}] {c.source}** (score {c.score:.3f})")
        lines.append(c.text.strip())
        lines.append("")
    lines.append(
        "_Tip: start Ollama (`ollama pull llama3.2`) or set `OPENAI_API_KEY` in `.env` for generated answers._"
    )
    return "\n".join(lines)


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> dict:
    user_prompt = build_user_prompt(question, chunks)
    used_fallback = False

    if settings.use_openai:
        try:
            answer = _generate_openai(user_prompt)
            backend = f"openai:{settings.openai_model}"
        except Exception as exc:
            answer = _extractive_fallback(question, chunks) + f"\n\n(OpenAI error: {exc})"
            backend = "extractive-fallback"
            used_fallback = True
    else:
        answer = _generate_ollama(user_prompt)
        backend = f"ollama:{settings.ollama_model}"
        if answer.startswith("Could not reach Ollama"):
            answer = _extractive_fallback(question, chunks)
            backend = "extractive-fallback"
            used_fallback = True

    return {
        "answer": answer,
        "backend": backend,
        "fallback": used_fallback,
        "sources": [
            {"source": c.source, "score": round(c.score, 4), "snippet": c.text[:240]}
            for c in chunks
        ],
    }


def _generate_openai(user_prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    resp = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    if not resp.choices or resp.choices[0].message is None:
        raise RuntimeError("OpenAI returned no completion")
    return (resp.choices[0].message.content or "").strip()


def _generate_ollama(user_prompt: str) -> str:
    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.2},
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            return (data.get("message", {}) or {}).get("content", "").strip() or str(data)
    except Exception as exc:
        return (
            "Could not reach Ollama. Start Ollama and pull a model, or set OPENAI_API_KEY in .env.\n"
            f"Details: {exc}"
        )
