# RecruitX — Installation Guide

> **Beginner-friendly step-by-step instructions for Windows, macOS, and Linux.**

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Before You Start — Install Python](#2-before-you-start--install-python)
3. [Download RecruitX](#3-download-recruitx)
4. [Set Up a Virtual Environment](#4-set-up-a-virtual-environment)
5. [Install Dependencies](#5-install-dependencies)
6. [Configure Environment Variables](#6-configure-environment-variables)
7. [Initialize the Database](#7-initialize-the-database)
8. [Build the FAISS Index](#8-build-the-faiss-index)
9. [Run the API Server](#9-run-the-api-server)
10. [Run the Dashboard (New Terminal)](#10-run-the-dashboard-new-terminal)
11. [Verify Everything Works](#11-verify-everything-works)
12. [Common Errors & Fixes](#12-common-errors--fixes)
13. [Uninstallation](#13-uninstallation)

---

## 1. System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| **Python** | 3.12 | 3.12 |
| **RAM** | 2 GB | 4 GB+ |
| **Disk space** | 1 GB | 2 GB (includes model cache) |
| **OS** | Windows 10+, macOS 11+, Ubuntu 20.04+ | Any modern OS |
| **Internet** | Required for first-time setup | Required |

### What you'll be installing

| Component | Purpose | Size |
|---|---|---|
| Python packages (21) | Web server, AI, database | ~150 MB |
| Sentence Transformer model | Convert text to vectors | ~80 MB |
| OpenRouter account (free) | AI analysis via API | Free |

### Optional hardware

- A GPU is **not required** — everything runs on CPU.
- A stable internet connection is needed for the first run (model download) and for AI features (OpenRouter API).

---

## 2. Before You Start — Install Python

> **If you already have Python 3.12 installed, skip to the next section.**

### Windows

1. Go to [python.org/downloads](https://python.org/downloads) and download **Python 3.12**.
2. Run the installer.
3. **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the installer.
4. Click **Install Now**.
5. Open **Command Prompt** (press `Win + R`, type `cmd`, hit Enter) and verify:

```batch
python --version
```

You should see something like `Python 3.12.4`.

### macOS

**Option A — Homebrew (recommended):**

```bash
brew install python@3.12
```

**Option B — Official installer:**

1. Go to [python.org/downloads](https://python.org/downloads) and download **Python 3.12**.
2. Run the `.pkg` installer.
3. Verify:

```bash
python3 --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
python3 --version
```

---

## 3. Download RecruitX

### Option A — Git clone (recommended)

```bash
git clone https://github.com/princitripathi/RecruitX.git
cd RecruitX
```

### Option B — Download ZIP

1. Go to [github.com/princitripathi/RecruitX](https://github.com/princitripathi/RecruitX).
2. Click the green **Code** button → **Download ZIP**.
3. Extract the ZIP file and open the folder.

---

## 4. Set Up a Virtual Environment

A virtual environment keeps RecruitX dependencies isolated from your other Python projects.

### Windows (Command Prompt)

```batch
python -m venv venv
venv\Scripts\activate
```

After activation, you should see `(venv)` at the beginning of your command prompt line.

### Windows (PowerShell)

If you use PowerShell, you may need to allow script execution first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
python -m venv venv
venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Verify it worked

```bash
# Which Python is active? (should point inside the venv folder)
which python
# or on Windows:
where python
```

You should see a path like `.../RecruitX/venv/bin/python` or `...\RecruitX\venv\Scripts\python.exe`.

---

## 5. Install Dependencies

With the virtual environment activated, run:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs all 21 packages listed in `requirements.txt`. The process may take **2–5 minutes** depending on your internet speed. Key packages include:

| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | Web server |
| `streamlit` | Dashboard UI |
| `sentence-transformers` | AI embeddings (downloads ~80 MB model) |
| `faiss-cpu` | Fast vector similarity search |
| `langchain` + `langchain-community` + `langchain-openai` + `openai` | LLM integration framework |
| `python-dotenv` | Load .env file into environment |
| `pydantic` + `pydantic-settings` | Data validation and settings |
| `pypdf` + `python-docx` | PDF/DOCX parsing |
| `pandas` + `numpy` | Data handling |
| `requests` | HTTP client for API calls |
| `scikit-learn` | ML utilities (normalization) |
| `plotly` | Charts |
| `pytest` | Testing |
| `black` | Code formatting |

### If installation fails

See [Common Errors & Fixes](#12-common-errors--fixes) section below.

---

## 6. Configure Environment Variables

RecruitX needs an API key from **OpenRouter** to power its AI agents.

### Step 1: Get a free OpenRouter API key

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys) and sign up (free).
2. Click **"Create Key"**, give it a name like "RecruitX", and copy the key.
3. The key looks like: `sk-or-v1-xxxxxxxxxxxx...`

### Step 2: Create the .env file

The project uses a `.env` file to store configuration. **This file contains secrets — never commit it to Git** (it's already in `.gitignore`).

Create a new file called `.env` in the `RecruitX` folder and paste the following template into it:

```ini
# RecruitX Environment Variables
# NEVER commit this file to GitHub!

# REQUIRED: OpenRouter API Key (Get from https://openrouter.ai/keys)
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# OpenRouter Configuration
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free

# Embedding Model (Local - no API key needed)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Database
DATABASE_PATH=data/recruitx.db

# FAISS Vector Store
FAISS_INDEX_PATH=data/faiss_index.bin
FAISS_ID_MAP_PATH=data/faiss_id_map.pkl

# Application Settings
APP_NAME=RecruitX
DEBUG=true

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Settings
STREAMLIT_PORT=8501

# Scoring Weights (must sum to 1.0)
WEIGHT_SEMANTIC=0.50
WEIGHT_SKILL=0.30
WEIGHT_SIGNAL=0.20

# OpenRouter LLM Settings
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
```

### Step 3: Paste your API key

Open `.env` in any text editor and replace `sk-or-v1-your-actual-key-here` with your real OpenRouter key:

```ini
OPENROUTER_API_KEY=sk-or-v1-the-key-you-copied-from-openrouter
```

### Full .env reference

Here is every variable available:

| Variable | Required | Default | What it does |
|---|---|---|---|
| `OPENROUTER_API_KEY` | **Yes** | — | Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |
| `OPENROUTER_MODEL` | No | `nvidia/nemotron-3-ultra-550b-a55b:free` | AI model for analysis (code fallback: `mistralai/mistral-7b-instruct:free`) |
| `EMBEDDING_MODEL` | No | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `EMBEDDING_DIMENSION` | No | `384` | Embedding vector size |
| `DATABASE_PATH` | No | `data/recruitx.db` | SQLite database file |
| `FAISS_INDEX_PATH` | No | `data/faiss_index.bin` | FAISS vector index file |
| `FAISS_ID_MAP_PATH` | No | `data/faiss_id_map.pkl` | FAISS ID lookup file |
| `APP_NAME` | No | `RecruitX` | Application display name |
| `APP_VERSION` | No | `1.0.0` | Application version |
| `API_HOST` | No | `0.0.0.0` | API server bind address |
| `API_PORT` | No | `8000` | API server port |
| `API_WORKERS` | No | `1` | Number of API worker processes |
| `STREAMLIT_PORT` | No | `8501` | Dashboard port |
| `WEIGHT_SEMANTIC` | No | `0.50` | Semantic score weight |
| `WEIGHT_SKILL` | No | `0.30` | Skill score weight |
| `WEIGHT_SIGNAL` | No | `0.20` | Signal score weight |
| `MIN_EXPERIENCE_RATIO` | No | `0.6` | Minimum experience match ratio |
| `MIN_SKILL_MATCH` | No | `0.3` | Minimum skill match threshold |
| `MAX_CANDIDATES_PER_SEARCH` | No | `20` | Max results per FAISS search |
| `LLM_TEMPERATURE` | No | `0.1` | AI creativity (0–1) |
| `LLM_MAX_TOKENS` | No | `2000` | Max AI response length |
| `LLM_MAX_RETRIES` | No | `3` | LLM call retry count |
| `LLM_TIMEOUT` | No | `30` | LLM request timeout (seconds) |
| `EMBEDDING_BATCH_SIZE` | No | `32` | Embedding batch size |
| `EMBEDDING_DEVICE` | No | `cpu` | Embedding compute device |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | No | `%(asctime)s - %(name)s - ...` | Log message format |
| `DEBUG` | No | `true` | Debug mode |

### Alternative free models (no credit card needed)

OpenRouter offers several free models. In `.env`, change:

```ini
OPENROUTER_MODEL=google/gemma-7b-it:free
```

Other free options:
- `nvidia/nemotron-3-ultra-550b-a55b:free` (set in `.env` by default)
- `google/gemma-7b-it:free`
- `meta-llama/llama-3-8b-instruct:free`

> **Note:** The code's built-in fallback (when `OPENROUTER_MODEL` is not set at all) is `mistralai/mistral-7b-instruct:free`. The template above explicitly sets it to `nvidia/nemotron-3-ultra-550b-a55b:free` for better results. You can use any of the options above.

---

## 7. Initialize the Database

This creates the SQLite database (`data/recruitx.db`) with all 5 tables, indexes, and **50 sample candidates**.

With the virtual environment **activated**, run:

```bash
python database/db_setup.py
```

### Expected output

```
============================================================
RecruitX Database Setup
============================================================
Database path: data/recruitx.db
✅ Connected to database
✅ Table 'candidates' created (or already exists)
✅ Table 'job_descriptions' created (or already exists)
✅ Table 'shortlists' created (or already exists)
✅ Table 'resumes' created (or already exists)
✅ Table 'chat_history' created (or already exists)
All 5 tables created successfully
✅ Index 'idx_candidates_skills' created (or already exists)
...
💯 Loaded 50 candidates from CSV into database
============================================================
✅ Database setup complete!
   50 candidates loaded from CSV
============================================================
```

### If you see "⏭️ Skipping CSV load"

This means the database already has data — that's fine. The script is safe to re-run.

---

## 8. Build the FAISS Index

The FAISS index powers the semantic (meaning-based) candidate search. It converts candidate profiles into vectors and stores them for fast similarity lookups.

With the virtual environment **activated**, run:

```bash
python scripts/build_index.py
```

### What happens

1. Reads all 50 candidates from the SQLite database.
2. Loads the Sentence Transformer model (`all-MiniLM-L6-v2` — ~80 MB download on first run).
3. Generates a 384-dimensional vector for each candidate.
4. Builds a FAISS `IndexFlatIP` (inner product = cosine similarity for normalized vectors).
5. Saves the index to `data/faiss_index.bin` and ID map to `data/faiss_id_map.pkl`.
6. Updates each candidate record in SQLite with its FAISS embedding ID.

### Expected output

```
============================================================
Starting FAISS Vector Index Build Pipeline
============================================================
Connecting to database: data/recruitx.db
Fetched 50 candidates from database.
Initializing CandidateEmbedder...
Generating embeddings in batch...
Initializing CandidateVectorStore...
Adding embeddings to vector store...
Saving index and ID map files...
Updating candidate records with embedding_id in SQLite...
Successfully updated 50 candidates with embedding_ids in SQLite.
============================================================
✅ FAISS Vector Index built successfully!
   Index saved to: data/faiss_index.bin
   ID Map saved to: data/faiss_id_map.pkl
   SQLite database updated with all embedding_ids.
============================================================
```

> **Note:** The first run downloads the Sentence Transformer model (~80 MB). This is a one-time download cached globally on your machine.

---

## 9. Run the API Server

With the virtual environment **activated**, start the FastAPI backend:

```bash
uvicorn api.main:app --reload --port 8000
```

### What to expect

```
INFO:     Will watch for changes in these directories: ['C:\\Users\\...\\RecruitX']
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     (Press CTRL+C to quit)
INFO:     Application startup complete.
INFO:     ============================================================
INFO:     RecruitX v1.0.0 starting up
INFO:     API docs: http://localhost:8000/docs
INFO:     ============================================================
```

### Key URLs

| Page | URL |
|---|---|
| **Swagger UI** (interactive API docs) | `http://localhost:8000/docs` |
| **ReDoc** (readable API docs) | `http://localhost:8000/redoc` |
| **Health check** | `http://localhost:8000/api/health` |

**Keep this terminal running.** Open a new terminal for the next step.

---

## 10. Run the Dashboard (New Terminal)

Open a **second terminal window** (Command Prompt, Terminal, or PowerShell) in the `RecruitX` folder.

Activate the virtual environment and start the Streamlit dashboard:

### Windows

```batch
venv\Scripts\activate
streamlit run frontend/dashboard.py
```

### macOS / Linux

```bash
source venv/bin/activate
streamlit run frontend/dashboard.py
```

### What to expect

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Your browser should open automatically to `http://localhost:8501`.

> **Note:** The dashboard connects to the API at `http://localhost:8000` by default. If your API is on a different host, set the `API_BASE_URL` environment variable before running the dashboard:
> ```bash
> # Windows
> set API_BASE_URL=http://your-server:8000
> # macOS / Linux
> export API_BASE_URL=http://your-server:8000
> ```

---

## 11. Verify Everything Works

### Method 1 — API health check (browser)

Open `http://localhost:8000/api/health` in your browser. You should see:

```json
{
  "status": "ok",
  "app": "RecruitX",
  "version": "1.0.0"
}
```

### Method 2 — API health check (command line)

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok","app":"RecruitX","version":"1.0.0"}
```

### Method 3 — Dashboard

1. Open `http://localhost:8501` in your browser.
2. You should see the RecruitX dark-themed dashboard.
3. In the sidebar, the **API** and **Database** status indicators should show green ("Online" / "Connected").

### Method 4 — Smoke test (recruit a candidate)

```bash
curl -X POST http://localhost:8000/api/recruit \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Looking for a Python developer with FastAPI experience.", "top_k": 3}'
```

This runs the full AI pipeline. You should get a ranked shortlist of the top 3 candidates with scores and explanations.

### Method 5 — Run the test suite

```bash
pytest tests/ -v --tb=short
```

This runs the **194 automated tests**. All should pass (or show only expected skips).

---

## 12. Common Errors & Fixes

### `python` not found / `command not found`

**Problem:** The terminal doesn't recognize the `python` command.

**Fix:**
- **Windows:** Reinstall Python and check **"Add Python to PATH"**. Restart Command Prompt.
- **macOS:** Use `python3` instead of `python`.
- **Linux:** `sudo apt install python3 python3-pip python3-venv`

### `pip` not found

**Fix:**
```bash
python -m pip install --upgrade pip
```
Or use `python3 -m pip` on macOS/Linux.

### `'pip' is not recognized` on Windows

**Fix:** Use `python -m pip install -r requirements.txt` instead of `pip install -r requirements.txt`.

### `venv` activation fails on Windows PowerShell

**Error:** `Execution Policy SecurityError`

**Fix:** Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Then retry activation.

### `ERROR: Could not install packages due to an OSError: [WinError 2]`

**Fix:** Close all programs that might be using the packages (e.g., other Python processes, IDEs). Delete the `venv` folder and redo Step 4.

### `ERROR: Could not find a version that satisfies the requirement faiss-cpu`

**Problem:** This typically happens on ARM-based Macs (Apple Silicon) or very old Python versions.

**Fix:**
```bash
pip install faiss-cpu --no-cache-dir
```
If it still fails on Apple Silicon:
```bash
pip install --upgrade pip
pip install --force-reinstall faiss-cpu
```

### `ModuleNotFoundError: No module named 'sentence_transformers'`

**Fix:** Ensure your virtual environment is activated, then reinstall:
```bash
pip install sentence-transformers
```

### `sqlite3.OperationalError: unable to open database file`

**Fix:** The `data/` directory must exist:
```bash
mkdir -p data   # macOS / Linux
mkdir data      # Windows
```
Or simply re-run `python database/db_setup.py` (it creates the directory automatically).

### `OPENROUTER_API_KEY` not set / `AuthenticationError`

**Fix:** 
1. Open `.env` and confirm the key is present and correct.
2. Make sure the key starts with `sk-or-v1-`.
3. Restart the API server (Ctrl+C, then re-run `uvicorn...`).
4. If using a free model, verify it's still free on [openrouter.ai/models](https://openrouter.ai/models).

### `HTTP 401` / `Insufficient credits` from OpenRouter

**Fix:** Free models have rate limits. Try:
- Using a different free model (change `OPENROUTER_MODEL` in `.env`).
- Checking your OpenRouter account balance.
- Waiting a few minutes between requests.

### `Port 8000 already in use`

**Problem:** Another program is using port 8000.

**Fix 1 — Kill the process:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS / Linux
lsof -i :8000
kill -9 <PID>
```

**Fix 2 — Use a different port:**
```bash
uvicorn api.main:app --reload --port 8001
```
Then update the dashboard by setting `API_BASE_URL=http://localhost:8001`.

### `Streamlit` dashboard shows blank page or connection error

**Fix:** Make sure the API server is running (see Step 9). The dashboard connects to the API at `http://localhost:8000`. Restart the dashboard if the API was started after it.

### `Error: FAISS index not found`

**Fix:** Run the index builder:
```bash
python scripts/build_index.py
```

### `Error: No candidates found`

**Fix:** Run the database setup:
```bash
python database/db_setup.py
```

### Tests fail with `ImportError`

**Fix:** Ensure the virtual environment is activated and you're running from the project root:
```bash
cd RecruitX
source venv/bin/activate   # or venv\Scripts\activate on Windows
pytest tests/ -v
```

### `pip install` is very slow

**Fix:** Use a faster package mirror:
```bash
# For users in China / Asia
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# For users in India
pip install -r requirements.txt -i https://mirror.nohup.in/pypi/simple
```

---

## 13. Uninstallation

To completely remove RecruitX from your system:

### Step 1: Stop the servers

Press `Ctrl + C` in both terminal windows (API server and dashboard).

### Step 2: Delete the project folder

```bash
# Make sure you're NOT inside RecruitX — go to its parent folder first
# Windows (Command Prompt)
cd ..
rmdir /s RecruitX

# macOS / Linux
cd ..
rm -rf RecruitX
```

### Step 3: (Optional) Remove the Python virtual environment

If you want to keep the source code but free up space:

```bash
# From inside the RecruitX folder
rmdir /s venv          # Windows
rm -rf venv            # macOS / Linux
```

### Step 4: (Optional) Remove the Sentence Transformer model cache

The embedding model (~80 MB) is cached globally:

- **Windows:** `C:\Users\<YourName>\.cache\huggingface\`
- **macOS / Linux:** `~/.cache/huggingface/`

Delete the `huggingface` folder to free up space.

### Step 5: (Optional) Uninstall Python

Only do this if you installed Python exclusively for RecruitX:
- **Windows:** Settings → Apps → Python 3.12 → Uninstall.
- **macOS:** If installed via Homebrew: `brew uninstall python@3.12`.
- **Linux:** `sudo apt remove python3.12`.

---

## Quick Reference — All Commands in Order

```bash
# 1. Clone & enter
git clone https://github.com/princitripathi/RecruitX.git
cd RecruitX

# 2. Create & activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
# Create .env (see Section 6) and set OPENROUTER_API_KEY

# 5. Initialize database
python database/db_setup.py

# 6. Build FAISS index
python scripts/build_index.py

# 7. Start API (keep open)
uvicorn api.main:app --reload --port 8000

# 8. In a NEW terminal, start dashboard
# Windows:
venv\Scripts\activate
streamlit run frontend/dashboard.py

# macOS / Linux:
source venv/bin/activate
streamlit run frontend/dashboard.py

# 9. Verify
# Open http://localhost:8000/api/health
# Open http://localhost:8501
```

---

## Getting Help

- **GitHub Issues:** [github.com/princitripathi/RecruitX/issues](https://github.com/princitripathi/RecruitX/issues)
- **OpenRouter Support:** [openrouter.ai](https://openrouter.ai)
- **Author:** Princi Tripathi — princitrp@gmail.com

---

*Last updated: July 2026*
