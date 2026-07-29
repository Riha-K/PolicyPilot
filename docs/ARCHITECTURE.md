# Architecture — PolicyPilot

## Goal

Answer customer questions using **company knowledge**, not model memorization. The system retrieves relevant policy chunks, then asks an LLM to answer **only from that context**.

## High-level diagram

```text
                 ┌──────────────────────────────┐
                 │     knowledge_base/          │
                 │  shipping · billing · returns│
                 │  support · faq (+ uploads)   │
                 └──────────────┬───────────────┘
                                │ ingest
                                ▼
                 ┌──────────────────────────────┐
                 │  Chunking (overlap windows)  │
                 └──────────────┬───────────────┘
                                │ embed
                                ▼
                 ┌──────────────────────────────┐
                 │ sentence-transformers        │
                 │ all-MiniLM-L6-v2             │
                 └──────────────┬───────────────┘
                                │ upsert
                                ▼
                 ┌──────────────────────────────┐
                 │ ChromaDB (data/chroma)       │
                 │ cosine similarity index      │
                 └──────────────▲───────────────┘
                                │ query top-k
┌──────────────┐   embed q      │
│ Streamlit UI │───────────────►│
│ chat + panel │                │
└──────┬───────┘                │
       │                        ▼
       │               retrieved chunks + scores
       │                        │
       │                        ▼
       │         ┌──────────────────────────────┐
       │         │ Grounded system prompt +     │
       │         │ user prompt (context+question│
       │         └──────────────┬───────────────┘
       │                        │
       │            ┌───────────┴───────────┐
       │            ▼                       ▼
       │     OpenAI API                 Ollama
       │   (if API key set)         (local default)
       │            └───────────┬───────────┘
       │                        ▼
       └──────────────────  answer + sources
```

## Runtime sequence (one question)

```text
User question
   → embed_query(question)
   → Chroma.query(top_k)
   → build prompt(context, question)
   → LLM.generate
   → Streamlit shows answer + source panel
```

## Components

| Module | Responsibility |
|--------|----------------|
| `app/streamlit_app.py` | Interactive UI, upload, reindex, chat history |
| `app/rag/chunking.py` | Split long docs into overlapping chunks |
| `app/rag/embeddings.py` | Local embedding model (cached) |
| `app/rag/store.py` | Persistent Chroma collection |
| `app/rag/ingest.py` | Read files, chunk, embed, upsert |
| `app/rag/generate.py` | System prompt + OpenAI/Ollama call |
| `app/rag/pipeline.py` | Orchestrates ensure → retrieve → generate |
| `app/config.py` | Env-driven settings |

## Why this design

| Choice | Reason |
|--------|--------|
| RAG instead of fine-tuning alone | Policies change often; reindex is cheaper than retraining |
| Local embeddings | No embedding API cost; works offline after first download |
| Chroma persistent store | Survives restarts; simple for a demo/deployable app |
| Grounded system prompt | Reduces hallucinations; answers cite policy constraints |
| Streamlit | Fast interactive UI; easy local + cloud deploy |
| OpenAI **or** Ollama | Works with cloud key or fully local demo |

## Data flow for ingest

```text
file bytes → text extract → chunks[] → vectors[] → Chroma upsert(id, doc, emb, meta)
```

Metadata stored per chunk:
- `source` — relative file path
- `index` — chunk number inside that file

## Trust / safety notes

- The LLM is instructed to refuse when context is insufficient.
- Still verify critical financial/legal answers against the original policy.
- Do not put real PII or production secrets into `knowledge_base/` for demos.

## Scaling path (interview talking points)

1. Replace Chroma with managed vector DB (Pinecone / pgvector)
2. Add hybrid search (BM25 + dense)
3. Add evaluation set (faithfulness / answer relevance)
4. Add auth + audit logs for agent usage
5. Add multi-tenant collections per brand/locale
