# Data Sources — Where Knowledge / Training Data Comes From

This file explains **what data this project uses**, where it comes from, and how that differs from “training a model.”

## Short answer

| Stage | Data used | Do we train? |
|-------|-----------|--------------|
| Retrieval index | Your CX documents in `knowledge_base/` | **No training** — documents are **embedded and indexed** |
| Answer generation | Same retrieved chunks + chat LLM | **No training by default** — we **prompt** Llama/GPT |
| Optional advanced | Domain Q&A pairs / preference data | Only if you follow `TRAINING_GUIDE.md` |

**Default project behavior = RAG indexing, not model training.**

---

## 1. Primary knowledge data (required for this app)

### Location

```text
knowledge_base/
  shipping.md
  billing.md
  returns.md
  support.md
  faq.txt
```

### What it is

Synthetic but realistic **customer-experience policy documents** written for this project:
- shipping SLAs, express rules, damage/lost package process
- billing, refund timelines, duplicate charges
- return windows (including electronics), exchanges
- support channels, escalations, security notes
- short FAQ snippets

### Why this format

| Format | Use |
|--------|-----|
| Markdown / TXT | Easy to edit; good for demos and Git |
| PDF (supported) | Mimics real policy PDFs from ops/legal |

### How it enters the system

1. Files are read at ingest / first app start
2. Split into chunks (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
3. Embedded with `sentence-transformers/all-MiniLM-L6-v2`
4. Stored in `data/chroma/`

### Replacing with *your* company data

Use the **same structure**, but swap content:

| Real-world source | How to add |
|-------------------|------------|
| Help Center / Zendesk export | Export articles → `.md` / `.txt` into `knowledge_base/` |
| Shipping SOP PDFs | Drop `.pdf` into `knowledge_base/` (text-extractable PDFs work best) |
| Returns policy Word docs | Save as `.txt` or `.md` |
| Internal Confluence pages | Copy relevant pages to markdown |
| Uploaded agent notes | Use Streamlit **Upload** (indexes immediately) |

Then click **Reindex knowledge base** in the sidebar (or delete `data/chroma` and restart).

> Do **not** commit confidential customer PII, passwords, or live order databases into this repo.

---

## 2. Embedding model data (downloaded, not trained here)

| Item | Detail |
|------|--------|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Source | Hugging Face Hub (downloaded on first run) |
| Trained by | Model authors (general English semantic similarity) |
| Your role | **Inference only** — encode chunks/queries |

You are **not** training this embedding model unless you follow the optional fine-tuning section in `TRAINING_GUIDE.md`.

---

## 3. Generation model data (OpenAI or Ollama)

| Backend | Model weights come from | Your data used as |
|---------|-------------------------|-------------------|
| OpenAI | Provider-hosted models | Prompt context only |
| Ollama (`llama3.2`, etc.) | Local pull via `ollama pull` | Prompt context only |

The CX documents are injected at **inference time** as retrieved context. They are not automatically used to update model weights.

---

## 4. Optional evaluation / training datasets (not shipped)

If you later want to measure or fine-tune quality, collect:

| Dataset type | Example fields | Source ideas |
|--------------|----------------|--------------|
| Gold Q&A | `question`, `ideal_answer`, `must_cite_source` | Support transcripts (anonymized), FAQ |
| Retrieval labels | `question`, `relevant_doc_ids` | Manual labeling by CX leads |
| Groundedness checks | `answer`, `context`, `supported?` | Human review or LLM-as-judge |

Suggested local folder (create when needed):

```text
data/training/
  qa_pairs.jsonl
  retrieval_labels.jsonl
```

Example `qa_pairs.jsonl` line:

```json
{"question":"What is the electronics return window?","answer":"15 days with accessories and seals intact.","source":"returns.md"}
```

---

## 5. What this project does *not* use

- Customer order databases
- Live payment gateway logs
- Scraped third-party websites (by default)
- Fine-tuned LoRA adapters (unless you add them later)

---

## 6. Interview-ready summary

> “PolicyPilot is grounded on a curated CX knowledge base. At runtime we embed those docs into Chroma. User questions retrieve top‑k chunks. The LLM answers only from that context. We don’t train the chat model on company data by default—updating policies means updating documents and reindexing, which is the operational advantage of RAG.”
