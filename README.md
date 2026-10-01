# PolicyPilot

Python assistant for customer-experience policy questions on shipping, billing, returns, and support. It retrieves the relevant policy text and answers only from that text, in a Streamlit chat.

## What it does

1. Read `.md`, `.txt`, and `.pdf` files from `knowledge_base/`
2. Split them into overlapping chunks
3. Embed the chunks with a local `sentence-transformers` model
4. Store the vectors in ChromaDB (`data/chroma/`)
5. For a question: embed it, retrieve the top matches, and ask the chat model to answer from those passages
6. Show the source passages in the Streamlit UI

Chat model:

- OpenAI, or any OpenAI-compatible API, when `OPENAI_API_KEY` is set
- otherwise Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`)

PolicyPilot does not fine-tune a chat model. It is retrieval plus an existing model. Optional embedding work is in [`docs/TRAINING_GUIDE.md`](docs/TRAINING_GUIDE.md).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, or start Ollama and pull a model:

```powershell
ollama pull llama3.2
streamlit run app/streamlit_app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`.

Command list, deploy steps, and fixes: [`RUNBOOK.md`](RUNBOOK.md).

Use **Python 3.11 or 3.12** if `torch`, `chromadb`, or `sentence-transformers` fail on 3.13.

## Defaults

Every value below can be overridden in `.env` (see `app/config.py`).

| Setting | Default |
| --- | --- |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 700 / 120 characters |
| `TOP_K` | 4 retrieved chunks |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `COLLECTION_NAME` | `policy_pilot` |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | `llama3.2` / `http://127.0.0.1:11434` |

## Layout

```text
app/streamlit_app.py          # chat UI
app/rag/                     # chunk, embed, store, answer
knowledge_base/              # sample policy docs
data/chroma/                 # local index, created at runtime
docs/ARCHITECTURE.md
docs/DATA_SOURCES.md
docs/TRAINING_GUIDE.md
```

## Example questions

- What is the standard shipping time for domestic orders?
- How do I request a refund for a duplicate charge?
- What is the return window for electronics?
- How can I contact support for a damaged package?
