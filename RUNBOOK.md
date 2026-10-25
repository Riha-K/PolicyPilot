# Runbook — PolicyPilot

All commands below assume **PowerShell on Windows**. Adjust paths if your clone lives elsewhere.

## 0. Prerequisites


| Need                                               | Why                      |
| -------------------------------------------------- | ------------------------ |
| Python 3.11+ (3.11/3.12 preferred)                 | App runtime              |
| ~2–4 GB free disk                                  | Embedding model + Chroma |
| [Ollama](https://ollama.com)                       | Answer generation        |
| Browser                                            | Streamlit UI             |


Check Python:

```powershell
python --version
```

## 1. Go to project folder

```powershell
cd path\to\PolicyPilot
```



## 2. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
```

Confirm prompt shows `(.venv)`.

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

First install downloads PyTorch / transformers wheels — can take several minutes.

### If install fails on Python 3.13

```powershell
deactivate
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```



## 4. Configure environment

```powershell
copy .env.example .env
notepad .env
```



### Local Ollama

```powershell
ollama serve
ollama pull llama3.2
```

`.env` defaults:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```



## 5. Run the Streamlit app (local)

From the project root with `.venv` active:

```powershell
cd path\to\PolicyPilot
.\.venv\Scripts\activate
streamlit run app/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

On first launch the app:

1. Downloads the embedding model (`all-MiniLM-L6-v2`) if missing
2. Ingests `knowledge_base/` into Chroma when the index is empty



## 6. Use the UI

1. Type a CX question in chat, or click an example in the right panel
2. Inspect **Retrieved context** (sources + scores)
3. Sidebar → **Reindex knowledge base** after editing files under `knowledge_base/`
4. Sidebar → upload `.txt` / `.md` / `.pdf` to append into the index



## 7. Smoke-test from Python (optional)

```powershell
.\.venv\Scripts\activate
python -c "from app.rag.pipeline import RAGPipeline; p=RAGPipeline(); print(p.ensure_ready()); print(p.ask('What is domestic shipping time?')['answer'][:400])"
```



## 8. Deploy (Streamlit Community Cloud)

1. Push this folder to a public/private GitHub repo (do **not** commit `.env` or `data/chroma/`).
2. Go to [https://share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Set:
  - Main file path: `app/streamlit_app.py`
  - Python version: 3.11 or 3.12
4. Cloud deploy needs a reachable Ollama host (local Ollama on your laptop is usually **not** available from Streamlit Cloud). Prefer LAN or a VPS with Ollama for demos.

1. Deploy and open the public URL.



### Local “deploy” alternative (LAN)

```powershell
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Other devices on the same network can open `http://<your-lan-ip>:8501`.

## 9. Reset the vector index

```powershell
Remove-Item -Recurse -Force .\data\chroma
```

Next app start will re-ingest `knowledge_base/`.

Or use the **Reindex** button in the sidebar.

## 10. Troubleshooting


| Symptom                    | Fix                                                         |
| -------------------------- | ----------------------------------------------------------- |
| `ModuleNotFoundError: app` | Run Streamlit from project root (`PolicyPilot`)             |
| Ollama errors in answer    | `ollama serve` + `ollama pull llama3.2`                     |
| Empty / weak answers       | Reindex; check `knowledge_base/` files exist                |
| Embedding download slow    | First run only; needs internet once                         |
| Chroma lock errors         | Stop all Streamlit processes, delete `data/chroma`, restart |
| Torch install fails        | Use Python 3.11/3.12 venv                                   |




## 11. Useful paths


| Path                  | Role                                 |
| --------------------- | ------------------------------------ |
| `path\to\PolicyPilot` | Project root — **run commands here** |
| `knowledge_base\`     | Source documents for retrieval       |
| `data\chroma\`        | Persistent vector DB                 |
| `.env`                | Secrets and model names              |
| `PolicyPilot.html`    | Open in browser for interview prep   |




## 12. Stop the app

In the Streamlit terminal: `Ctrl + C`.