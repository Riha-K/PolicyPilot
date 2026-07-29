"""Streamlit UI for PolicyPilot."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.rag.pipeline import RAGPipeline

st.set_page_config(
    page_title="PolicyPilot",
    page_icon="💬",
    layout="wide",
)


@st.cache_resource(show_spinner="Loading embedding model & vector store...")
def get_pipeline() -> RAGPipeline:
    pipe = RAGPipeline()
    pipe.ensure_ready()
    return pipe


def main() -> None:
    st.title("PolicyPilot")
    st.caption(
        "Grounded CX policy Q&A. Answers use retrieved knowledge-base chunks "
        "(shipping, billing, returns, support)."
    )

    with st.sidebar:
        st.header("Controls")
        top_k = st.slider("Top-K chunks", min_value=1, max_value=8, value=settings.top_k)
        st.markdown("---")
        st.subheader("Index")
        pipe = get_pipeline()
        health = pipe.health()
        st.write(f"**Chunks in store:** {health['chunks']}")
        st.write(f"**LLM backend:** `{health['llm']}`")
        st.write(f"**Embeddings:** `{health['embedding_model']}`")

        if st.button("Reindex knowledge base", use_container_width=True):
            with st.spinner("Rebuilding vector index..."):
                get_pipeline.clear()
                pipe = get_pipeline()
                result = pipe.reindex()
            st.success(f"Indexed {result.get('chunks', 0)} chunks from {result.get('files', 0)} files.")
            st.rerun()

        uploaded = st.file_uploader(
            "Upload extra .txt / .md / .pdf into index",
            type=["txt", "md", "pdf"],
        )
        if uploaded is not None and st.button("Ingest upload", use_container_width=True):
            suffix = Path(uploaded.name).suffix or ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = Path(tmp.name)
            with st.spinner("Embedding & indexing upload..."):
                result = pipe.ingest_file(tmp_path)
            st.success(f"Added {result.get('chunks', 0)} chunks. Store total: {result.get('total_in_store', 0)}")
            st.rerun()

        st.markdown("---")
        st.markdown(
            "**Setup tip:** set `OPENAI_API_KEY` in `.env`, or run Ollama "
            f"(`{settings.ollama_model}`) at `{settings.ollama_base_url}`."
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_chat, col_ctx = st.columns([1.35, 1.0], gap="large")

    with col_chat:
        st.subheader("Chat")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("Sources used"):
                        for s in msg["sources"]:
                            st.markdown(f"- **{s['source']}** (score {s['score']})")

        prompt = st.chat_input("Ask about shipping, billing, returns, or support…")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Retrieving context & generating answer..."):
                    result = pipe.ask(prompt, top_k=top_k)
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                st.markdown(answer)
                st.caption(f"Backend: `{result.get('backend')}`")
                if sources:
                    with st.expander("Sources used", expanded=False):
                        for s in sources:
                            st.markdown(f"- **{s['source']}** (score {s['score']})")
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
                st.session_state.last_result = result

    with col_ctx:
        st.subheader("Retrieved context")
        last = st.session_state.get("last_result")
        if not last:
            st.info("Ask a question to inspect retrieved chunks here.")
        else:
            for i, src in enumerate(last.get("sources", []), start=1):
                with st.expander(f"[{i}] {src['source']} — score {src['score']}", expanded=(i == 1)):
                    st.write(src.get("snippet", ""))

        st.markdown("---")
        st.subheader("Try these")
        examples = [
            "What is the standard shipping time for domestic orders?",
            "How do I request a refund for a duplicate charge?",
            "What is the return window for electronics?",
            "How can I contact support for a damaged package?",
        ]
        for ex in examples:
            if st.button(ex, use_container_width=True, key=f"ex_{ex[:24]}"):
                st.session_state.pending_example = ex
                st.rerun()

        if st.session_state.get("pending_example"):
            example = st.session_state.pop("pending_example")
            st.session_state.messages.append({"role": "user", "content": example})
            result = pipe.ask(example, top_k=top_k)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result.get("answer", ""),
                    "sources": result.get("sources", []),
                }
            )
            st.session_state.last_result = result
            st.rerun()


if __name__ == "__main__":
    main()
