<div align="center">
  <h1>RecruitX</h1>
  <p><strong>Autonomous Multi-Agent AI Recruitment System</strong></p>
  <p><em>From job description to ranked shortlist with explainable scores</em></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/Streamlit-1.37-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
    <img src="https://img.shields.io/badge/LangChain-0.2-1C3C3C?logo=langchain&logoColor=white" alt="LangChain">
    <img src="https://img.shields.io/badge/FAISS-CPU-546E7A" alt="FAISS">
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  </p>
</div>

### Key Highlights

- Multi-Agent AI Platform
- AI Resume Parsing
- Semantic Search (FAISS)
- Explainable Candidate Ranking
- Skill Gap Analysis
- AI Recruiter Chat
- Interview Question Generator
- FastAPI + Streamlit
- 194 Automated Tests

---

## Overview

RecruitX is a full-stack AI recruitment assistant that automates the end-to-end candidate screening pipeline. Submit a job description — the system analyzes requirements, searches candidates by semantic meaning, scores each profile on skill fit and behavioral signals, and returns a ranked shortlist with transparent score breakdowns — all within seconds.

Powered by five specialized AI agents coordinated through a central orchestrator, RecruitX combines LLM-powered job understanding (OpenRouter), vector similarity search (FAISS + Sentence Transformers), weighted scoring, skill gap analysis, and a rule-based behavioral signal analyzer. The recruiter can interact via a Streamlit dashboard or REST API, using natural language to discover candidates and generate personalized interview questions.

---

## Why RecruitX?

Traditional applicant tracking systems rely on keyword matching, missing the context and nuance in candidate profiles. RecruitX replaces manual screening with an automated, multi-dimensional evaluation pipeline that is faster, more consistent, and fully transparent.

- **Automate the screening pipeline** — Go from raw job description to ranked shortlist without manual effort
- **Understand every score** — Each candidate's rank decomposes into semantic, skill, and signal components with full transparency
- **Apply consistent criteria** — Formula-based scoring eliminates subjective variability across candidates
- **Reduce time-to-shortlist** — Full pipeline completes in under two minutes

---

## Features

- **Resume Upload & AI Parsing** — Upload PDF/DOCX resumes; auto-extract, MD5-deduplicate, and index candidates into the system
- **Candidate Search & Ranking** — Semantic search combined with skill and signal scoring to rank candidates by relevance to the JD
- **Skill Gap Analysis** — Visual identification of matched, missing, and bonus skills per candidate against job requirements
- **Interview Question Generation** — LLM-generated questions targeting each candidate's specific skill gaps
- **AI Recruiter Chat** — Natural language interface for recruiter queries (e.g., "Python devs in Bangalore with 3+ years")
- **Explainable Scoring** — Weighted formula (Semantic × 50% + Skill × 30% + Signal × 20%) with per-candidate score breakdowns
- **Semantic Search** — Sentence Transformer embeddings + FAISS vector similarity for meaning-based candidate matching
- **Multi-Agent Architecture** — Five specialized AI agents (JD Analyst, Candidate Ranker, Signal Analyzer, Chat Agent, Orchestrator) working in concert
- **Interactive Dashboard** — Streamlit UI with four tabs: Find Candidates, Chat, Database, Analytics
- **CSV Export** — Download shortlists for offline review and sharing
- **Feedback Loop** — Recruiter thumbs-up/thumbs-down feedback stored for future ranking improvements
- **Duplicate Detection** — MD5 file hashing + email uniqueness to prevent duplicate entries

---

## Technology Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Language** | Python 3.12 | Core runtime |
| **LLM Provider** | OpenRouter (nvidia/nemotron-3-ultra-550b-a55b:free / mistralai/mistral-7b-instruct:free) | JD analysis, resume parsing, chat, question generation |
| **LLM Framework** | LangChain | Agent orchestration, prompt chaining |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) | Local 384-dim text-to-vector encoding |
| **Vector Search** | FAISS-CPU (IndexFlatIP) | Cosine-similarity candidate retrieval |
| **Backend** | FastAPI + Uvicorn | REST API with auto-generated OpenAPI docs |
| **Database** | SQLite | Zero-configuration persistent storage |
| **Frontend** | Streamlit | Python-native recruiter dashboard |
| **Resume Parsing** | pypdf, python-docx | PDF and DOCX text extraction |
| **Data Processing** | pandas, numpy, scikit-learn | Candidate data manipulation |
| **Visualization** | Plotly | Interactive score charts and analytics |
| **Testing** | pytest | Unit and integration test suite |
| **Deployment** | Render (free tier) | One-click blueprint deployment |

---

## Architecture

```
                        ┌─────────────────┐
                        │    Recruiter     │
                        │ (Job Description)│
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Orchestrator   │
                        │     Agent       │
                        │(Coordinates all)│
                        └──┬─────┬─────┬──┘
                           │     │     │
              ┌────────────┘     │     └────────────┐
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐
     │  JD Analyst    │ │  Candidate   │ │ Signal Analyzer  │
     │    Agent       │ │   Ranker     │ │     Agent        │
     │  (LLM-based)   │ │ (FAISS-based)│ │ (Algorithmic)    │
     └───────┬────────┘ └──────┬───────┘ └────────┬─────────┘
             │                 │                   │
             └─────────────────┼───────────────────┘
                               ▼
                     ┌─────────────────┐
                     │  Scoring Engine │
                     │ (Weighted 50/30/20)│
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Skill Gap       │
                     │ Analyzer        │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Interview       │
                     │ Question Gen.   │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Ranked Shortlist│
                     │ + Explanations  │
                     └─────────────────┘
```

### Agents

| Agent | Module | Method | Responsibility |
|-------|--------|--------|---------------|
| **JD Analyst** | `agents/jd_analyst.py` | LLM (OpenRouter) | Extracts requirements, skills, experience, seniority from raw JD text |
| **Candidate Ranker** | `agents/candidate_ranker.py` | FAISS vector search | Retrieves top-N candidates by semantic similarity to JD |
| **Signal Analyzer** | `agents/signal_analyzer.py` | Rule-based algorithm | Scores profile completeness, recency, and experience fit |
| **Chat Agent** | `agents/chat_agent.py` | LLM + keyword fallback | Processes natural language recruiter queries |
| **Orchestrator** | `agents/orchestrator.py` | Coordination | Runs the full pipeline: analyze → search → score → rank → persist |

### Scoring Formula

```
Final Score = (Semantic × 0.50) + (Skill × 0.30) + (Signal × 0.20)
```

| Component | Weight | Calculation |
|-----------|--------|------------|
| **Semantic Score** | 50% | FAISS inner-product similarity on L2-normalized JD & candidate embeddings, normalized to [0, 100] |
| **Skill Score** | 30% | (Required skills match × 0.70) + (Preferred skills match × 0.30), each as percentage overlap |
| **Signal Score** | 20% | (Profile completeness × 0.40) + (Recency × 0.40) + (Experience match × 0.20) |

---

## Project Structure

```
RecruitX/
├── agents/                    # AI agents (business logic)
│   ├── orchestrator.py        # Pipeline coordinator
│   ├── jd_analyst.py          # JD analysis via LLM
│   ├── candidate_ranker.py    # FAISS semantic search
│   ├── signal_analyzer.py     # Behavioral signal scoring
│   └── chat_agent.py          # Natural language chat interface
├── api/                       # FastAPI backend
│   ├── main.py                # App entry point + middleware
│   ├── models.py              # Pydantic request/response schemas
│   └── routes/
│       ├── recruitment.py     # POST /api/recruit, /api/feedback
│       ├── candidates.py      # CRUD /api/candidates
│       ├── resumes.py         # POST /api/upload-resume
│       ├── chat.py            # POST /api/chat
│       └── interviews.py      # POST /api/interview-questions
├── database/                  # SQLite data layer
│   ├── models.py              # Table definitions + indexes
│   ├── db_setup.py            # DB initialization + sample data
│   └── crud.py                # All CRUD operations
├── embeddings/                # Vector search layer
│   ├── embedder.py            # SentenceTransformer encoding
│   ├── vector_store.py        # FAISS index management
│   └── build_index.py         # Index builder script
├── scoring/                   # Scoring and analysis
│   ├── scoring_engine.py      # Weighted scoring formula
│   └── skill_gap.py           # Skill gap classification
├── utils/                     # Utilities
│   ├── resume_parser.py       # PDF/DOCX text extraction + LLM parsing
│   └── interview_generator.py # LLM-based question generation
├── frontend/                  # Streamlit dashboard
│   └── dashboard.py           # Full recruiter UI (4 tabs)
├── tests/                     # pytest suite (13 test files, ~4000 lines)
│   ├── conftest.py            # Shared fixtures
│   ├── test_api.py            # API endpoint tests
│   ├── test_orchestrator.py   # Pipeline integration tests
│   ├── test_scoring.py        # Scoring engine tests
│   ├── test_resume_parser.py  # Resume parsing tests
│   └── ... (13 test files total)
├── data/                      # Data files
│   ├── sample_candidates.csv  # 50 Indian candidate profiles
│   ├── sample_jds/            # 3 sample job descriptions
│   ├── faiss_index.bin        # FAISS vector index (auto-generated)
│   ├── faiss_id_map.pkl       # FAISS ID mapping (auto-generated)
│   └── validate_candidates.py # CSV validation script
├── docs/                      # Documentation
│   ├── API_REFERENCE.md       # REST API reference (10 endpoints)
│   ├── ARCHITECTURE.md        # System architecture
│   └── PROJECT_STRUCTURE.md   # Project organization guide
├── backups/                   # Database and FAISS index backups
├── uploads/                   # Uploaded resume files (UUID-named)
├── check_db.py                # Quick SQLite inspection script
├── .env                       # Environment variables (not in Git)
├── .gitignore
├── INSTALL.md                 # Installation guide
├── LICENSE                    # MIT License
├── requirements.txt           # Python dependencies
├── render.yaml                # Render deployment blueprint
└── README.md                  # This file
```

---

## Installation

> **Full installation instructions are in [INSTALL.md](./INSTALL.md).**

Quick start:

```bash
# Clone the repository
git clone https://github.com/princitripathi/RecruitX.git
cd RecruitX

# Create and activate virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (set OPENROUTER_API_KEY in .env)
cp .env.example .env

# Initialize database with 50 sample candidates
python database/db_setup.py

# Build FAISS vector index
python embeddings/build_index.py

# Start API server (port 8000)
uvicorn api.main:app --reload --port 8000

# Start dashboard (port 8501) in a separate terminal
streamlit run frontend/dashboard.py
```

### Access Points

| Service | URL |
|---------|-----|
| **API Docs (Swagger UI)** | `http://localhost:8000/docs` |
| **API Docs (ReDoc)** | `http://localhost:8000/redoc` |
| **Health Check** | `http://localhost:8000/api/health` |
| **Dashboard** | `http://localhost:8501` |

---

## API Overview

> **Complete API reference is in [docs/API_REFERENCE.md](./docs/API_REFERENCE.md).**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Server health check |
| `POST` | `/api/recruit` | Run recruitment pipeline → ranked shortlist |
| `GET` | `/api/candidates` | List all candidates |
| `POST` | `/api/candidates` | Add a new candidate |
| `GET` | `/api/candidates/{id}` | Get candidate details |
| `DELETE` | `/api/candidates/{id}` | Delete a candidate |
| `POST` | `/api/upload-resume` | Upload and parse a PDF/DOCX resume |
| `POST` | `/api/chat` | Natural language recruiter query |
| `POST` | `/api/feedback` | Submit ranking feedback (good/bad) |
| `POST` | `/api/interview-questions` | Generate personalized interview questions |

### Quick Example

```bash
curl -X POST http://localhost:8000/api/recruit \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Python backend engineer with FastAPI and PostgreSQL experience.",
    "top_k": 5
  }'
```

Response includes a sorted shortlist with each candidate's semantic, skill, and signal scores plus a human-readable explanation.

---

## Configuration

Key environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | **Required.** OpenRouter API key |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b:free` | LLM model for analysis |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `WEIGHT_SEMANTIC` | `0.50` | Semantic score weight |
| `WEIGHT_SKILL` | `0.30` | Skill score weight |
| `WEIGHT_SIGNAL` | `0.20` | Signal score weight |
| `LLM_TEMPERATURE` | `0.1` | LLM response creativity |
| `LLM_MAX_TOKENS` | `2000` | Maximum LLM response length |
| `DATABASE_PATH` | `data/recruitx.db` | SQLite database file location |

---

## Testing

The project includes 13 test files with comprehensive unit and integration tests.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run a specific test file
pytest tests/test_scoring.py -v

# Run API tests only
pytest tests/test_api.py -v
```

---

## Sample Data

The project ships with **50 realistic Indian candidate profiles** across 12 cities, with skills ranging from Python and Java to Kubernetes and Go. Three sample job descriptions are included:

| File | Role |
|------|------|
| `data/sample_jds/software_engineer.txt` | Python/FastAPI backend engineer |
| `data/sample_jds/data_scientist.txt` | ML and data science role |
| `data/sample_jds/product_manager.txt` | Technical product manager |

---

## Deployment

RecruitX can be deployed to Render's free tier in two clicks using `render.yaml`:

1. Push the repository to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect your repository
4. Add `OPENROUTER_API_KEY` as a **Secret** in the service settings
5. Deploy

The pre-deploy command automatically runs `database/db_setup.py` and `embeddings/build_index.py`. See [render.yaml](./render.yaml) for full configuration.

> **Note:** Render's free tier spins down after 15 minutes of inactivity. The first request after spin-down may take ~30 seconds (cold start).

---

## Database Schema

The SQLite database contains five tables:

| Table | Purpose |
|-------|---------|
| `candidates` | Candidate profiles with skills, experience, location, and activity data |
| `job_descriptions` | Parsed JD analysis results |
| `shortlists` | Ranking results with per-candidate scores and recruiter feedback |
| `resumes` | Uploaded resume metadata with MD5 hash for deduplication |
| `chat_history` | Session-based conversation logs |

---

## Future Improvements

- **Scheduler Agent** — Interview scheduling with calendar integration
- **Feedback-Driven Learning** — Use recruiter feedback to re-rank future searches
- **Resume Parser Webhook** — Asynchronous resume processing for large uploads
- **Authentication & Authorization** — Multi-tenant recruiter accounts
- **Advanced Analytics** — Hiring funnel metrics, source effectiveness, time-to-hire trends
- **CI/CD Pipeline** — Automated testing and deployment with GitHub Actions
- **Docker Support** — Containerized deployment for any cloud provider

---

## Screenshots

*Coming after final UI polish.*

Planned screenshots:
- Dashboard overview
- Resume upload workflow
- Candidate ranking results
- AI Recruiter Chat interface
- Interview question generator

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

**Princi Tripathi** — B.Tech Computer Science, 4th Year

- GitHub: https://github.com/princitripathi
- LinkedIn: https://www.linkedin.com/in/princi-tripathi
- Email: princitrp@gmail.com

---

<div align="center">
  <p><strong>RecruitX</strong> demonstrates how modern AI techniques — LLM-powered agents, vector search embeddings, and explainable scoring formulas — can be composed into a practical, deployable recruitment automation system. Built with Python, FastAPI, Streamlit, LangChain, and FAISS.</p>
  <p>
    <a href="https://github.com/princitripathi/RecruitX">GitHub</a> •
    <a href="http://localhost:8000/docs">API Docs</a> •
    <a href="http://localhost:8501">Dashboard</a>
  </p>
</div>
