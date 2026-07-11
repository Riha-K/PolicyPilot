# Training Guide — When and How to Train (Step by Step)

## Important first

**You do not need to train a model to run this project.**

Default pipeline:

1. Index documents (embed + store)
2. Retrieve chunks
3. Generate with an existing chat model (OpenAI / Ollama)

Use this guide only if an interviewer asks “how would you train/improve it?” or you want higher domain quality.

---

## Path A — No training (recommended baseline)

### Steps

1. Put policies in `knowledge_base/`
2. Run Streamlit / click **Reindex**
3. Answer questions via RAG

### Improve quality without training

| Action | Effect |
|--------|--------|
| Cleaner source docs | Better chunks |
| Tune `CHUNK_SIZE` / `CHUNK_OVERLAP` | Better retrieval granularity |
| Increase `TOP_K` carefully | More context (may add noise) |
| Stronger chat model | Better phrasing / instruction following |
| Better system prompt | Fewer hallucinations |

---

## Path B — Evaluate before training

Create a small gold set (20–50 questions):

```text
data/training/qa_pairs.jsonl
```

For each question, manually note:
- correct answer
- which file should be retrieved

Measure:
- **Retrieval hit rate** — is the right doc in top‑k?
- **Answer faithfulness** — does the answer stick to context?

Only move to training if retrieval is good but generation is weak, or retrieval itself is weak.

---

## Path C — Fine-tune embeddings (optional, advanced)

Use when similar CX questions retrieve the wrong policy sections.

### High-level steps

1. Build pairs: `(query, positive_passage [, negative_passage])` from support logs
2. Start from `all-MiniLM-L6-v2`
3. Contrastive / MultipleNegativesRanking fine-tune with Sentence-Transformers
4. Save to `models/cx-embedder/`
5. Set in `.env`:

```env
EMBEDDING_MODEL=models/cx-embedder
```

6. Delete `data/chroma` and reindex

### Minimal command sketch (reference only)

```powershell
# After preparing train data and a fine-tune script (not required for demo)
python scripts/finetune_embeddings.py --train data/training/retrieval_pairs.jsonl --out models/cx-embedder
```

> A full fine-tune script is intentionally not required for the demo app.

---

## Path D — Fine-tune / adapt the chat model (optional, advanced)

Use when the model ignores instructions, formats poorly, or needs brand tone.

### Prefer order of effort

1. Prompt engineering + better retrieval (cheapest)
2. Few-shot examples in the prompt
3. LoRA/QLoRA on domain Q&A (GPU recommended)
4. Full fine-tune (rarely needed)

### LoRA sketch with Ollama-compatible workflow

1. Export Q&A as instruction JSONL
2. Fine-tune with Unsloth / Axolotl / Hugging Face TRL on a base instruct model
3. Export GGUF / adapter
4. Serve via Ollama or vLLM
5. Point `.env` `OLLAMA_MODEL` / OpenAI-compatible endpoint to the new model

### Steps checklist

- [ ] Anonymize all customer data
- [ ] Split train/validation
- [ ] Train LoRA on instruction pairs
- [ ] Evaluate faithfulness on held-out CX questions
- [ ] Only then replace production model id

---

## Path E — What “training data” means in interviews

Be precise:

| Phrase people say | What they often mean |
|-------------------|----------------------|
| “Train the RAG” | Usually **index documents**, not backprop |
| “Train embeddings” | Fine-tune sentence encoder |
| “Train the LLM” | SFT / LoRA / RLHF on chat model |
| “Feed PDFs to the model” | Ambiguous — clarify ingest vs fine-tune |

**Best answer for this repo:**  
“We index policy PDFs/markdown into a vector store. The generator is a frozen chat model. If needed, we’d fine-tune embeddings or LoRA the generator using anonymized support Q&A.”

---

## GPU / time expectations (rough)

| Task | Hardware | Time scale |
|------|----------|------------|
| Demo RAG ingest (sample KB) | CPU | minutes |
| Embedding fine-tune (small) | GPU 8–16GB | hours |
| LLM LoRA | GPU 16GB+ | hours–days |

---

## Safety

- Strip PII before any fine-tune
- Keep evaluation set that checks for invented refund amounts / fake policies
- Prefer RAG updates for policy changes; use training for style/skill, not daily policy edits
