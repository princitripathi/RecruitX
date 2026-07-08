# RecruitX — Autonomous Multi-Agent AI Recruitment System

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https.shields.io/badge/FastAPI-0.111-green?logo=fastapi&logoColor=white)
![Streamlit](https.shields.io/badge/Streamlit-1.37-red?logo=streamlit&logoColor=white)
![LangChain](https.shields.io/badge/LangChain-0.2-orange?logo=langchain&logoColor=white)
![FAISS](https.shields.io/badge/FAISS-CPU-yellow)
![License](https.shields.io/badge/License-MIT-purple)

> **RecruitX** automates candidate screening using a team of AI agents. Paste a job description → get a ranked shortlist with explanations in under 2 minutes.

---

## Problem Statement

Recruiters spend **70% of their time** manually screening hundreds of resumes. RecruitX solves this by using multiple specialized AI agents that work together to:

1. **Analyze** job descriptions → extract structured requirements
2. **Search** candidate database semantically → find relevant matches
3. **Score** candidates holistically → skills + experience + behavioral signals
4. **Explain** every ranking → transparent, auditable decisions
5. **Generate** interview questions → targeted to skill gaps

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RECRUITER                                  │
│                    (Job Description)                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT                              │
│              (Coordinates all other agents)                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ JD ANALYST    │    │ CANDIDATE     │    │ SIGNAL        │
│ AGENT         │    │ RANKER        │    │ ANALYZER      │
│ (LLM)         │    │ (FAISS)       │    │ (Algorithmic) │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                  ┌─────────────────────┐
                  │ SCORING ENGINE      │
                  │ (Weighted Formula)  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ SKILL GAP ANALYZER  │
                  │ INTERVIEW GENERATOR │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ RANKED SHORTLIST    │
                  │ + EXPLANATIONS      │
                  └─────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **LLM** | OpenRouter (Mistral-7B Free) | Job analysis, chat, questions |
| **Embeddings** | all-MiniLM-L6-v2 (Local) | Semantic search vectors |
| **Vector Search** | FAISS-CPU | Fast similarity search |
| **Backend** | FastAPI + Uvicorn | REST API |
| **Database** | SQLite | Zero-config storage |
| **Frontend** | Streamlit | Python-only dashboard |
| **Parsing** | PyPDF2, python-docx | Resume text extraction |

---

## Scoring Formula

```
Final Score = (Semantic × 0.50) + (Skill × 0.30) + (Signal × 0.20)
```

| Component | Weight | Description |
|-----------|--------|-------------|
| **Semantic** | 50% | FAISS cosine similarity (JD ↔ Candidate) |
| **Skill** | 30% | Required (70%) + Preferred (30%) skill match |
| **Signal** | 20% | Profile completeness (40%) + Recency (40%) + Experience match (20%) |

---

## Features

✅ **Multi-Agent Architecture** — 6 specialized agents working together  
✅ **Semantic Search** — Vector embeddings + FAISS for meaning-based matching  
✅ **Explainable AI** — Every ranking has a human-readable explanation  
✅ **Skill Gap Analysis** — Visual breakdown of matched/missing/bonus skills  
✅ **Interview Question Generator** — Personalized questions per candidate  
✅ **Chat Interface** — Natural language queries ("Python devs in Bangalore with 3+ years")  
✅ **Resume Parser** — Upload PDF/DOCX, auto-extract and index  
✅ **Feedback Loop** — Recruiter 👍/👎 improves future rankings  
✅ **Full Dashboard** — 4 tabs: Find Candidates, Chat, Database, Analytics  

---

## Quick Start

### Prerequisites
- Python 3.12+
- OpenRouter API Key (free at [openrouter.ai](https://openrouter.ai/keys))
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/RecruitX.git
cd RecruitX

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env  # Then edit .env with your OpenRouter API key
# Or just edit .env directly

# 5. Setup database with sample data
python database/db_setup.py

# 6. Build FAISS vector index
python embeddings/build_index.py

# 7. Start API server (Terminal 1)
uvicorn api.main:app --reload --port 8000

# 8. Start Dashboard (Terminal 2)
streamlit run frontend/dashboard.py
```

### Access Points
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **Health Check**: http://localhost:8000/api/health

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/recruit` | Get ranked shortlist for a job description |
| `GET` | `/api/candidates` | List all candidates |
| `POST` | `/api/candidates` | Add new candidate |
| `GET` | `/api/candidates/{id}` | Get candidate details |
| `DELETE` | `/api/candidates/{id}` | Delete candidate |
| `POST` | `/api/upload-resume` | Upload & parse PDF/DOCX resume |
| `POST` | `/api/chat` | Natural language recruiter queries |
| `POST` | `/api/feedback` | Submit ranking feedback (👍/👎) |
| `GET` | `/api/health` | Health check |

### Example: Recruit Endpoint
```bash
curl -X POST http://localhost:8000/api/recruit \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We need a Python developer with FastAPI and SQL experience...",
    "top_k": 10
  }'
```

---

## Project Structure

```
RecruitX/
├── agents/              # AI Agents (6 agents)
│   ├── orchestrator.py  # Master coordinator
│   ├── jd_analyst.py    # Job description analyzer
│   ├── candidate_ranker.py  # FAISS semantic search
│   ├── signal_analyzer.py   # Behavioral signals
│   ├── chat_agent.py    # Natural language interface
│   └── scheduler.py     # Interview scheduling
├── database/            # SQLite layer
│   ├── db_setup.py      # Initialize DB + sample data
│   ├── models.py        # Table schemas
│   └── crud.py          # CRUD operations
├── embeddings/          # Vector search
│   ├── embedder.py      # Text → vectors
│   ├── vector_store.py  # FAISS index management
│   └── build_index.py   # Build/rebuild index
├── scoring/             # Scoring & ranking
│   ├── scoring_engine.py  # Weighted formula
│   └── skill_gap.py       # Skill gap analysis
├── api/                 # FastAPI backend
│   ├── main.py          # App + middleware
│   ├── models.py        # Pydantic models
│   └── routes/          # API endpoints
├── frontend/            # Streamlit dashboard
│   └── dashboard.py     # Complete UI
├── utils/               # Utilities
│   ├── resume_parser.py     # PDF/DOCX parsing
│   ├── interview_generator.py  # Question generation
│   ├── logger.py            # Logging setup
│   └── helpers.py           # Common functions
├── data/                # Data files
│   ├── sample_candidates.csv  # 50 Indian profiles
│   ├── sample_jds/            # Sample job descriptions
│   └── (auto-generated FAISS files)
├── tests/               # Pytest suite
├── docs/                # Documentation
├── .env                 # Secrets (NOT in Git)
├── requirements.txt     # Dependencies
├── render.yaml          # Deployment config
└── README.md            # This file
```

---

## Sample Data

The project includes **50 realistic Indian candidate profiles** with:
- Names, emails, phones, locations (Mumbai, Delhi, Bangalore, etc.)
- Skills: Python, Java, React, ML, SQL, Docker, AWS, etc.
- Experience: 0–10 years
- Education: B.Tech, BCA, M.Tech, etc.
- Profile completeness: 40–100%
- Last active: 1–400 days ago

Sample Job Descriptions:
- `data/sample_jds/software_engineer.txt`
- `data/sample_jds/data_scientist.txt`
- `data/sample_jds/product_manager.txt`

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scoring.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

---

## Deployment (Render.com Free Tier)

1. Push to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. New → Blueprint → Connect your repo
4. Add `OPENROUTER_API_KEY` as **Secret** in service settings
5. Deploy! (Auto-runs `db_setup.py` and `build_index.py`)

> **Note**: Free tier spins down after 15 min inactivity. First request after spin-down takes ~30s (cold start).

---

## Configuration

Key settings in `.env`:

```env
# Required
OPENROUTER_API_KEY=your_key_here

# Model (free options)
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free

# Scoring weights (must sum to 1.0)
WEIGHT_SEMANTIC=0.50
WEIGHT_SKILL=0.30
WEIGHT_SIGNAL=0.20
```

---

## Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT License — Feel free to use for your final year project!

---

## Author

**Princi Tripathi**  
B.Tech Computer Science, 4th Year  
[GitHub](https://github.com/yourusername) • [LinkedIn](https://linkedin.com/in/yourprofile)

---

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) for free LLM access
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [LangChain](https://langchain.com/) for agent orchestration
- [Streamlit](https://streamlit.io/) for rapid UI development

---

⭐ **Star this repo if RecruitX helps you build an impressive final year project!**