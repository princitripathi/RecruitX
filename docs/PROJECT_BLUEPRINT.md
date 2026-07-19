# RecruitX Project Blueprint

This document captures the original implementation blueprint created before development began.

It includes the planned architecture, milestones, implementation strategy, and technical decisions that guided the project from concept to completion.

This document is preserved for reference and historical context. The current implementation is documented in the README and the other files under the docs/ directory.

---

# RecruitX — Master Implementation Guide
> **This document is a self-contained blueprint for building RecruitX from scratch.**
> If you are an AI assistant helping build this project, read this entire document before writing any code.
> Every decision, architecture choice, file, and feature is documented here.

---

## 👩‍💻 Project Owner
- **Name:** Princi Tripathi
- **Degree:** B.Tech Computer Science, 4th Year
- **Goal:** Build an impressive final year project that stands out to hiring managers and recruiters
- **Skill Level:** Knows Python basics, not an advanced coder — needs clear explanations with every code block
- **OS:** Windows
- **Editor:** VS Code
- **Python:** 3.12 (installed)
- **API Key:** OpenRouter API Key (not OpenAI directly)

---

## 🎯 Project Summary

**RecruitX** is an Autonomous Multi-Agent AI Recruitment System.

It solves a real problem: recruiters waste 70% of their time manually screening hundreds of candidate profiles. RecruitX automates this entirely using AI agents.

**How it works in one line:**
> Recruiter pastes a job description → RecruitX AI agents autonomously search, score, and rank candidates → Recruiter receives a ranked shortlist with explanations in under 2 minutes.

**This is NOT a Redrob-specific tool.** It works for any company, any recruiter, any job portal.

---

## 🏆 What Makes This Project Stand Out

1. Multi-agent AI architecture (not just a single model)
2. Semantic search using vector embeddings (FAISS)
3. Explainable AI — every ranking has a human-readable reason
4. Full stack: FastAPI backend + Streamlit frontend
5. Resume PDF parser
6. Chat interface for recruiters (natural language queries)
7. Skill gap analysis per candidate
8. Interview question generator
9. Recruiter feedback loop for continuous improvement
10. Deployed live with complete GitHub documentation

---

## 🛠️ Complete Tech Stack

| Layer | Tool | Version | Why |
|---|---|---|---|
| Language | Python | 3.12 | All AI libraries are Python |
| LLM API | OpenRouter | latest | Free models available, supports multiple LLMs |
| LLM Framework | LangChain | latest | Agent orchestration |
| Embeddings | Sentence Transformers | latest | all-MiniLM-L6-v2 model, free, 384 dimensions |
| Vector Search | FAISS-CPU | latest | Fast semantic search |
| Backend | FastAPI | latest | Modern, fast REST API |
| Server | Uvicorn | latest | ASGI server for FastAPI |
| Database | SQLite | built-in | No setup needed, stores candidates |
| Frontend | Streamlit | latest | Python-only UI, no HTML/CSS needed |
| PDF Parsing | PyPDF2 | latest | Extract text from resumes |
| Word Parsing | python-docx | latest | Extract text from .docx resumes |
| Data | Pandas | latest | Data processing |
| Validation | Pydantic | latest | API request/response validation |
| Config | python-dotenv | latest | Environment variables |
| Testing | pytest | latest | Unit and integration tests |
| Deployment | Render.com | free tier | Live deployment |
| Version Control | Git + GitHub | latest | Portfolio and collaboration |

### OpenRouter Configuration
```
Base URL: https://openrouter.ai/api/v1
Free Model: mistralai/mistral-7b-instruct:free
Alternative 1: google/gemma-7b-it:free
Alternative 2: meta-llama/llama-3-8b-instruct:free
```

### Embedding Model
```
Model: all-MiniLM-L6-v2
Dimension: 384
Size: ~80MB
Speed: Embeds 1000 profiles in seconds
Cost: FREE, no API key needed
```

---

## 📁 Complete Project Structure

```
RecruitX/
│
├── agents/                         # All AI agents
│   ├── __init__.py
│   ├── orchestrator.py             # Master coordinator — connects all agents
│   ├── jd_analyst.py               # Analyzes job descriptions using LLM
│   ├── candidate_ranker.py         # Semantic matching using FAISS
│   ├── signal_analyzer.py          # Behavioral signal scoring (no LLM)
│   ├── scheduler.py                # Interview scheduling agent
│   └── chat_agent.py               # Chat interface for recruiter queries
│
├── database/                       # Database layer
│   ├── __init__.py
│   ├── db_setup.py                 # Create tables, load sample data
│   ├── models.py                   # SQLite table schemas
│   └── crud.py                     # Create, Read, Update, Delete operations
│
├── embeddings/                     # Vector search layer
│   ├── __init__.py
│   ├── embedder.py                 # Text to vector conversion
│   ├── vector_store.py             # FAISS index management
│   └── build_index.py              # Script to rebuild entire FAISS index
│
├── scoring/                        # Scoring and ranking
│   ├── __init__.py
│   ├── scoring_engine.py           # Weighted scoring formula
│   └── skill_gap.py                # Skill gap analysis per candidate
│
├── api/                            # FastAPI backend
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, middleware, startup
│   ├── models.py                   # Pydantic request/response models
│   └── routes/
│       ├── __init__.py
│       ├── recruitment.py          # POST /api/recruit
│       ├── candidates.py           # CRUD for candidates
│       ├── resumes.py              # Resume upload endpoint
│       └── chat.py                 # Chat interface endpoint
│
├── frontend/                       # Streamlit UI
│   └── dashboard.py                # Complete recruiter dashboard
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── resume_parser.py            # PDF/DOCX parser
│   ├── interview_generator.py      # Generate interview questions
│   ├── logger.py                   # Logging setup
│   └── helpers.py                  # Common helper functions
│
├── data/                           # Data files
│   ├── sample_candidates.csv       # 50 fake Indian candidate profiles
│   ├── sample_jds/                 # Sample job descriptions
│   │   ├── software_engineer.txt
│   │   ├── data_scientist.txt
│   │   └── product_manager.txt
│   ├── faiss_index.bin             # FAISS vector index (auto-generated)
│   └── faiss_id_map.pkl            # FAISS ID to candidate ID map (auto-generated)
│
├── tests/                          # All tests
│   ├── test_scoring.py
│   ├── test_signal_analyzer.py
│   ├── test_jd_analyst.py
│   ├── test_resume_parser.py
│   └── test_integration.py
│
├── docs/                           # Documentation
│   ├── architecture.md
│   ├── api_docs.md
│   └── user_guide.md
│
├── .vscode/
│   ├── launch.json                 # VS Code debug configurations
│   └── settings.json               # VS Code settings
│
├── .env                            # API keys — NEVER push to GitHub
├── .gitignore                      # Files to exclude from GitHub
├── requirements.txt                # All Python dependencies
├── render.yaml                     # Render deployment config
└── README.md                       # Professional GitHub README
```

---

## 🗄️ DATABASE SCHEMA

### Complete SQLite Tables

```sql
-- TABLE 1: candidates
CREATE TABLE IF NOT EXISTS candidates (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    name                  TEXT NOT NULL,
    email                 TEXT UNIQUE NOT NULL,
    phone                 TEXT,
    location              TEXT,
    skills                TEXT NOT NULL,
    experience_years      REAL NOT NULL DEFAULT 0,
    education             TEXT,
    previous_roles        TEXT,
    profile_completeness  INTEGER DEFAULT 0,
    last_active_days      INTEGER DEFAULT 999,
    resume_path           TEXT,
    embedding_id          INTEGER,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 2: job_descriptions
CREATE TABLE IF NOT EXISTS job_descriptions (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    title                 TEXT NOT NULL,
    raw_text              TEXT NOT NULL,
    required_skills       TEXT,
    preferred_skills      TEXT,
    min_experience        REAL DEFAULT 0,
    education_required    TEXT,
    seniority_level       TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 3: shortlists
CREATE TABLE IF NOT EXISTS shortlists (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    jd_id                 INTEGER NOT NULL,
    candidate_id          INTEGER NOT NULL,
    final_score           REAL NOT NULL,
    semantic_score        REAL NOT NULL,
    skill_score           REAL NOT NULL,
    signal_score          REAL NOT NULL,
    rank                  INTEGER NOT NULL,
    explanation           TEXT,
    recruiter_feedback    INTEGER DEFAULT NULL,  -- 1=good, 0=bad (feedback loop)
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

-- TABLE 4: resumes
CREATE TABLE IF NOT EXISTS resumes (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id          INTEGER,
    file_name             TEXT NOT NULL,
    file_path             TEXT NOT NULL,
    file_hash             TEXT UNIQUE NOT NULL,
    parsed_text           TEXT,
    upload_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

-- TABLE 5: chat_history (for chat interface)
CREATE TABLE IF NOT EXISTS chat_history (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id            TEXT NOT NULL,
    role                  TEXT NOT NULL,  -- 'user' or 'assistant'
    message               TEXT NOT NULL,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates(skills);
CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(experience_years);
CREATE INDEX IF NOT EXISTS idx_shortlists_jd ON shortlists(jd_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_resumes_hash ON resumes(file_hash);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
```

---

## 🔢 SCORING FORMULA

This is the core intelligence of RecruitX. Every candidate gets a score out of 100.

```
Final Score = (Semantic Score × 0.50) + (Skill Score × 0.30) + (Signal Score × 0.20)
```

### Semantic Score (50%)
- Uses FAISS cosine similarity between JD vector and candidate profile vector
- Range: 0 to 100
- Normalized from FAISS inner product score

### Skill Score (30%)
```
Skill Score = (Required Skills Match × 0.70) + (Preferred Skills Match × 0.30)
Required Skills Match = (matched required skills / total required skills) × 100
Preferred Skills Match = (matched preferred skills / total preferred skills) × 100
```

### Signal Score (20%)
```
Signal Score = (Profile Completeness × 0.40) + (Recency Score × 0.40) + (Experience Match × 0.20)

Recency Score:
  last_active_days <= 7   → 100
  last_active_days <= 30  → 80
  last_active_days <= 90  → 60
  last_active_days <= 180 → 40
  last_active_days <= 365 → 20
  last_active_days > 365  → 5

Experience Match:
  ratio = candidate_experience / required_experience
  ratio >= 1.0  → 100
  ratio >= 0.8  → 80
  ratio >= 0.6  → 60
  else          → 30
```

---

## 🤖 AGENT RESPONSIBILITIES

### 1. Orchestrator Agent (orchestrator.py)
- Receives job description from API
- Calls JD Analyst Agent → gets structured JD requirements
- Calls Vector Store search → gets top 20 semantic matches
- Fetches candidate details from SQLite database
- Calls Signal Analyzer for each candidate
- Calls Scoring Engine to calculate final scores
- Calls Skill Gap Analyzer for each candidate
- Sorts and returns top K ranked candidates

### 2. JD Analyst Agent (jd_analyst.py)
- Input: raw job description text
- Uses OpenRouter LLM with structured output parser
- Output: JDAnalysis object with:
  - required_skills: list of strings
  - preferred_skills: list of strings
  - min_experience_years: float
  - education_required: string
  - seniority_level: string (Junior/Mid/Senior/Lead)
  - role_summary: string
  - search_query: optimized string for FAISS search
- Has retry logic (3 attempts on failure)
- Temperature: 0.1 for consistent outputs

### 3. Candidate Ranker Agent (candidate_ranker.py)
- Input: search query from JD Analyst
- Uses FAISS vector store to find top K candidates
- Returns: list of {candidate_id, semantic_score}

### 4. Signal Analyzer Agent (signal_analyzer.py)
- Input: candidate dict, required_experience float
- Pure algorithmic — no LLM needed
- Returns: {signal_score, recency_score, completeness_score, experience_match}

### 5. Chat Agent (chat_agent.py)
- Input: recruiter natural language query + conversation history
- Examples: "Show Python developers with 3+ years", "Who has the highest signal score?"
- Uses LLM to parse query and filter/sort candidates accordingly
- Maintains conversation memory within session

### 6. Scheduler Agent (scheduler.py)
- Input: candidate details + recruiter preferences
- Generates interview time slot suggestions
- Future: Google Calendar integration

---

## ✨ ADVANCED FEATURES TO IMPLEMENT

### Feature 1: AI Resume Parser
- Upload PDF or DOCX resume
- Extract text using PyPDF2 / python-docx
- Clean extracted text (remove extra spaces, special chars)
- Use LLM to parse into structured candidate profile
- Detect duplicates using MD5 file hash
- Auto-add to database and FAISS index

### Feature 2: Chat Interface
- Recruiter types natural language: "Find Python developers in Mumbai with 3+ years"
- LangChain agent parses intent
- Filters database accordingly
- Returns results conversationally
- Maintains chat history in SQLite

### Feature 3: Skill Gap Analysis
- For each shortlisted candidate, show:
  - Skills they HAVE that match the JD ✅
  - Skills they are MISSING from the JD ❌
  - Skills they have that are BONUS (not in JD) ⭐
- Display as color-coded skill tags in dashboard

### Feature 4: Interview Question Generator
- Input: candidate resume + job description
- Uses LLM to generate 5-10 personalized interview questions
- Questions target skill gaps and verify claimed experience
- Output displayed in dashboard under each candidate

### Feature 5: Recruiter Feedback Loop
- After viewing shortlist, recruiter can mark each candidate as 👍 or 👎
- Feedback stored in shortlists.recruiter_feedback column
- Future model can use this data to improve rankings

### Feature 6: Resume-JD Visualization
- Radar chart showing candidate scores across dimensions
- Bar chart comparing top 10 candidates
- All charts built with Streamlit native charts or Plotly

---

## 📋 SAMPLE DATA SPECIFICATION

### sample_candidates.csv (50 rows)
Columns:
```
id, name, email, phone, location, skills, experience_years, education,
previous_roles, profile_completeness, last_active_days
```

Rules for sample data:
- Use realistic Indian names (Rahul, Priya, Amit, Neha, etc.)
- Use Indian cities (Mumbai, Delhi, Bangalore, Hyderabad, Pune, Chennai)
- Skills should be realistic tech stacks
- Experience: mix of 0-10 years
- Profile completeness: mix of 40-100%
- Last active days: mix of 1-400 days

Example rows:
```
1,Rahul Sharma,rahul.sharma@gmail.com,9876543210,Bangalore,"Python,ML,FastAPI,SQL",3,B.Tech CS,"Data Analyst at TCS",90,5
2,Priya Singh,priya.singh@gmail.com,9876543211,Mumbai,"Java,Spring Boot,MySQL,Docker",5,B.Tech IT,"Backend Dev at Infosys",75,45
3,Amit Kumar,amit.kumar@gmail.com,9876543212,Delhi,"Python,Django,React,PostgreSQL",2,BCA,"Junior Dev at Wipro",60,120
```

---

## 🔌 API ENDPOINTS SPECIFICATION

| Method | Endpoint | Description | Request Body | Response |
|---|---|---|---|---|
| POST | /api/recruit | Get ranked shortlist | {job_description, top_k} | {success, shortlist, jd_analysis, processing_time_ms} |
| GET | /api/candidates | Get all candidates | - | {candidates: [...]} |
| POST | /api/candidates | Add candidate | CandidateCreate | {candidate, message} |
| GET | /api/candidates/{id} | Get one candidate | - | {candidate} |
| DELETE | /api/candidates/{id} | Delete candidate | - | {message} |
| POST | /api/upload-resume | Upload PDF/DOCX | file (multipart) | {candidate, message} |
| POST | /api/chat | Chat query | {message, session_id} | {response, candidates} |
| POST | /api/feedback | Submit ranking feedback | {shortlist_id, feedback} | {message} |
| GET | /api/health | Health check | - | {status, version} |

---

## 🎨 FRONTEND LAYOUT SPECIFICATION

### Dashboard Tabs:
1. **🔍 Find Candidates** — Main recruitment tab
   - Large text area for job description
   - "Find Best Candidates" button
   - Progress bar while processing
   - Stats row: candidates found, total searched, top score, processing time
   - Ranked candidate cards (expandable) showing all scores + explanation
   - Skill gap tags per candidate
   - Interview questions button per candidate
   - Export to CSV button

2. **💬 Chat with RecruitX** — Natural language interface
   - Chat input box
   - Conversation history
   - Results displayed inline

3. **👥 Candidate Database** — Browse all candidates
   - Search and filter
   - Add candidate manually
   - Upload resume

4. **📊 Analytics** — Dashboard stats
   - Score distribution chart
   - Top skills in demand
   - Candidate activity heatmap

---

## 🚀 DEVELOPMENT PHASES & ORDER

Build in this exact order — each phase depends on the previous:

| Phase | Task | Key Files | Estimated Days |
|---|---|---|---|
| 0 | Environment setup | venv, .env, folders | 1 |
| 1 | Sample data creation | data/sample_candidates.csv | 1 |
| 2 | Database setup | database/db_setup.py, models.py, crud.py | 2 |
| 3 | Embedder | embeddings/embedder.py | 1 |
| 4 | Vector store | embeddings/vector_store.py, build_index.py | 2 |
| 5 | Signal analyzer | agents/signal_analyzer.py | 1 |
| 6 | Scoring engine | scoring/scoring_engine.py | 1 |
| 7 | JD analyst agent | agents/jd_analyst.py | 2 |
| 8 | Candidate ranker | agents/candidate_ranker.py | 1 |
| 9 | Skill gap analyzer | scoring/skill_gap.py | 1 |
| 10 | Orchestrator | agents/orchestrator.py | 2 |
| 11 | FastAPI backend | api/main.py, routes/ | 3 |
| 12 | Streamlit frontend | frontend/dashboard.py | 4 |
| 13 | Resume parser | utils/resume_parser.py | 2 |
| 14 | Chat interface | agents/chat_agent.py, api/routes/chat.py | 3 |
| 15 | Interview generator | utils/interview_generator.py | 1 |
| 16 | Testing | tests/ | 2 |
| 17 | GitHub + README | README.md, docs/ | 2 |
| 18 | Deployment | render.yaml | 1 |

**Total: ~33 days for complete professional project**

---

## ⚙️ ENVIRONMENT & CONFIG FILES

### requirements.txt
```
langchain
langchain-community
langchain-openai
openai
sentence-transformers
faiss-cpu
fastapi
uvicorn
streamlit
pandas
numpy
pypdf2
python-docx
python-dotenv
pydantic
requests
scikit-learn
plotly
pytest
black
```

### .env
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=mistralai/mistral-7b-instruct:free
DATABASE_PATH=data/recruitx.db
FAISS_INDEX_PATH=data/faiss_index.bin
FAISS_ID_MAP_PATH=data/faiss_id_map.pkl
MAX_UPLOAD_SIZE_MB=10
TOP_K_DEFAULT=10
```

### .gitignore
```
venv/
.env
__pycache__/
*.pyc
*.pyo
data/recruitx.db
data/faiss_index.bin
data/faiss_id_map.pkl
uploads/
.vscode/settings.json
```

### .vscode/launch.json
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["api.main:app", "--reload", "--port", "8000"],
            "env": {"PYTHONPATH": "${workspaceFolder}"}
        },
        {
            "name": "Run Streamlit",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": ["run", "frontend/dashboard.py"]
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"]
        }
    ]
}
```

### render.yaml
```yaml
services:
  - type: web
    name: recruitx-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENROUTER_API_KEY
        sync: false
      - key: OPENROUTER_BASE_URL
        value: https://openrouter.ai/api/v1
      - key: MODEL_NAME
        value: mistralai/mistral-7b-instruct:free
```

---

## 📏 CODING STANDARDS (follow always)

```python
# 1. Classes: PascalCase
class JDAnalystAgent:
class VectorStore:

# 2. Functions: snake_case
def analyze_job_description():
def calculate_skill_score():

# 3. Constants: UPPER_SNAKE_CASE
EMBEDDING_DIMENSION = 384
FAISS_INDEX_PATH = "data/faiss_index.bin"

# 4. Always use type hints
def calculate_final_score(semantic: float, skill: float, signal: float) -> float:

# 5. Always add docstrings
def analyze(self, jd_text: str) -> JDAnalysis:
    """
    Analyze job description and return structured requirements.
    Args:
        jd_text: Raw job description string
    Returns:
        JDAnalysis object with extracted requirements
    Raises:
        Exception: If LLM fails after 3 retries
    """

# 6. Always handle exceptions specifically
try:
    result = agent.analyze(jd)
except ValueError as e:
    logger.error("Invalid input: %s", str(e))
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error("Unexpected error: %s", str(e))
    raise HTTPException(status_code=500, detail="Internal server error")

# 7. Always use logging not print
import logging
logger = logging.getLogger(__name__)
logger.info("Pipeline started")
logger.error("Failed: %s", str(e))
```

---

## 🔐 SECURITY RULES (always follow)

1. Never hardcode API keys — always use os.getenv()
2. Never push .env to GitHub — always add to .gitignore
3. Validate all file uploads (type + size)
4. Sanitize all text inputs (remove HTML chars)
5. Always check file hash before saving resume (duplicate detection)

---

## 🧪 TESTING RULES

Every module must have tests in tests/ folder.
Run tests with: `pytest tests/ -v`

Minimum tests required:
- test_scoring.py: perfect match, no match, score range, ranking order
- test_signal_analyzer.py: recency scores, experience match
- test_jd_analyst.py: output structure validation
- test_resume_parser.py: PDF text extraction, duplicate detection
- test_integration.py: full pipeline end to end

---

## 📝 HOW TO RUN THE PROJECT

```bash
# Step 1: Activate virtual environment
cd Desktop/RecruitX
venv\Scripts\activate

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Setup database with sample data
python database/db_setup.py

# Step 4: Build FAISS vector index
python embeddings/build_index.py

# Step 5: Start API server (Terminal 1)
uvicorn api.main:app --reload --port 8000

# Step 6: Start Dashboard (Terminal 2)
streamlit run frontend/dashboard.py

# Step 7: Open browser
# API docs: http://localhost:8000/docs
# Dashboard: http://localhost:8501

# Step 8: Run tests
pytest tests/ -v
```

---

## 📌 INSTRUCTIONS FOR AI ASSISTANT

If you are an AI tool helping Princi build this project:

1. **Read this entire document first** before writing any code
2. **Always explain code** — Princi is learning, so add comments to every function
3. **Build one phase at a time** — do not skip phases
4. **Always check phase number** — ask "which phase are we on?" if unsure
5. **Use exactly the file paths** defined in the project structure above
6. **Follow the coding standards** defined in this document
7. **Use OpenRouter** not OpenAI directly (base_url must be set)
8. **Windows paths** — use backslash or os.path for file paths
9. **After each phase** — remind Princi to test before moving to next phase
10. **If a library version causes errors** — suggest the fix immediately
11. **Keep code beginner-friendly** — avoid overly complex patterns
12. **Current progress tracker** — always ask Princi which phase is complete before starting new code

---

*RecruitX Master Guide v1.0 — By Princi Tripathi | Built with ❤️*
