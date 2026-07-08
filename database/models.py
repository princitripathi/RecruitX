"""
database/models.py — SQLite Table Schemas for RecruitX

This module defines all SQL CREATE TABLE statements and indexes
for the RecruitX database. These are the exact schemas from the
Master Guide.

Tables:
    1. candidates       — Candidate profiles (skills, experience, etc.)
    2. job_descriptions  — Parsed job description data
    3. shortlists        — Ranked candidates per JD with scores
    4. resumes           — Uploaded resume files and parsed text
    5. chat_history      — Chat conversation logs

Usage:
    from database.models import ALL_TABLES, ALL_INDEXES
"""

# ============================================================
# TABLE 1: candidates
# Stores all candidate profiles loaded from CSV or added via API.
# The 'embedding_id' links to the FAISS vector index position.
# ============================================================
CREATE_CANDIDATES_TABLE = """
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
"""

# ============================================================
# TABLE 2: job_descriptions
# Stores raw JD text and the structured analysis from the
# JD Analyst Agent (required skills, preferred skills, etc.)
# ============================================================
CREATE_JOB_DESCRIPTIONS_TABLE = """
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
"""

# ============================================================
# TABLE 3: shortlists
# Stores the ranked results for each recruitment run.
# Each row = one candidate scored against one JD.
# 'recruiter_feedback' enables the feedback loop feature:
#   1 = recruiter liked the match (good)
#   0 = recruiter disliked the match (bad)
#   NULL = no feedback yet
# ============================================================
CREATE_SHORTLISTS_TABLE = """
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
    recruiter_feedback    INTEGER DEFAULT NULL,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);
"""

# ============================================================
# TABLE 4: resumes
# Stores uploaded resume files with deduplication via MD5 hash.
# 'parsed_text' holds the extracted text from PDF/DOCX.
# ============================================================
CREATE_RESUMES_TABLE = """
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
"""

# ============================================================
# TABLE 5: chat_history
# Stores conversation logs for the recruiter chat interface.
# 'role' is either 'user' or 'assistant'.
# 'session_id' groups messages within a single chat session.
# ============================================================
CREATE_CHAT_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS chat_history (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id            TEXT NOT NULL,
    role                  TEXT NOT NULL,
    message               TEXT NOT NULL,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ============================================================
# INDEXES — Improve query performance on frequently searched columns
# ============================================================
CREATE_INDEX_CANDIDATES_SKILLS = """
CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates(skills);
"""

CREATE_INDEX_CANDIDATES_EXPERIENCE = """
CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(experience_years);
"""

CREATE_INDEX_SHORTLISTS_JD = """
CREATE INDEX IF NOT EXISTS idx_shortlists_jd ON shortlists(jd_id);
"""

CREATE_INDEX_CANDIDATES_EMAIL = """
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
"""

CREATE_INDEX_RESUMES_HASH = """
CREATE INDEX IF NOT EXISTS idx_resumes_hash ON resumes(file_hash);
"""

CREATE_INDEX_CHAT_SESSION = """
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
"""

# ============================================================
# Grouped lists for easy iteration in db_setup.py
# ============================================================

# All table creation statements in dependency order
ALL_TABLES = [
    ("candidates", CREATE_CANDIDATES_TABLE),
    ("job_descriptions", CREATE_JOB_DESCRIPTIONS_TABLE),
    ("shortlists", CREATE_SHORTLISTS_TABLE),
    ("resumes", CREATE_RESUMES_TABLE),
    ("chat_history", CREATE_CHAT_HISTORY_TABLE),
]

# All index creation statements
ALL_INDEXES = [
    ("idx_candidates_skills", CREATE_INDEX_CANDIDATES_SKILLS),
    ("idx_candidates_experience", CREATE_INDEX_CANDIDATES_EXPERIENCE),
    ("idx_shortlists_jd", CREATE_INDEX_SHORTLISTS_JD),
    ("idx_candidates_email", CREATE_INDEX_CANDIDATES_EMAIL),
    ("idx_resumes_hash", CREATE_INDEX_RESUMES_HASH),
    ("idx_chat_session", CREATE_INDEX_CHAT_SESSION),
]
