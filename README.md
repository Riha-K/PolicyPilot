# PolicyPilot

AI-powered customer support assistant that **retrieves** policy knowledge and **generates grounded answers** for shipping, billing, returns, and support questions.

Interactive UI: **Streamlit** (local or Streamlit Community Cloud).

## What it does

1. Ingests documents from `knowledge_base/` (`.md`, `.txt`, `.pdf`)
2. Splits them into overlapping chunks
3. Embeds chunks with a local `sentence-transformers` model
4. Stores vectors in **ChromaDB** (`data/chroma/`)
5. For each question: embed → top‑k retrieve → LLM answer with a grounded system prompt
6. Shows retrieved sources in the Streamlit UI

LLM backends:
- **OpenAI** (or any OpenAI-compatible API) when `OPENAI_API_KEY` is set
- otherwise **Ollama** at `OLLAMA_BASE_URL` / `OLLAMA_MODEL`

> PolicyPilot does **not** fine-tune a custom LLM by default. It uses retrieval + an existing chat model (RAG). Optional embedding / domain fine-tuning steps are documented in [`docs/TRAINING_GUIDE.md`](docs/TRAINING_GUIDE.md).

## Quick start

```powershell
cd e:\Projects\PolicyPilot
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Then either set `OPENAI_API_KEY` in `.env`, **or** start Ollama and pull a model:

```powershell
ollama pull llama3.2
```

Run the app:

```powershell
streamlit run app/streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

Full command list: [`RUNBOOK.md`](RUNBOOK.md).

## Project layout

```text
PolicyPilot/
├── app/
│   ├── config.py
│   ├── streamlit_app.py          # Deployable Streamlit UI
│   └── rag/
│       ├── chunking.py
│       ├── embeddings.py
│       ├── store.py              # ChromaDB
│       ├── ingest.py
│       ├── generate.py           # OpenAI / Ollama
│       └── pipeline.py
├── knowledge_base/               # Sample CX policy docs
├── data/chroma/                  # Local vector index (created at runtime)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   └── TRAINING_GUIDE.md
├── PolicyPilot.html              # Interview guide (open in browser)
├── RUNBOOK.md
├── README.md
├── requirements.txt
└── .env.example
```

## Example questions

- What is the standard shipping time for domestic orders?
- How do I request a refund for a duplicate charge?
- What is the return window for electronics?
- How can I contact support for a damaged package?

## Docs map

| File | Purpose |
|------|---------|
| [`RUNBOOK.md`](RUNBOOK.md) | Exact commands: install, run, deploy, troubleshoot |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design + diagrams |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | Where knowledge / training data comes from |
| [`docs/TRAINING_GUIDE.md`](docs/TRAINING_GUIDE.md) | Step-by-step when (and when not) to train |
| [`PolicyPilot.html`](PolicyPilot.html) | Interview prep (open in browser) |

## Python version note

Use **Python 3.11 or 3.12** if `torch` / `chromadb` / `sentence-transformers` fail on 3.13.

## Resume one-liner

**PolicyPilot** — Fast retrieval over CX policy docs with local embeddings (Chroma) and grounded answers via OpenAI/Ollama, exposed through a Streamlit chat UI.
