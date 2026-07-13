# RecruitX API Reference

> **Version:** 1.0.0 | **Base URL:** `http://localhost:8000` | **Schema:** REST over HTTP/JSON

## Overview

RecruitX exposes a RESTful JSON API with 10 endpoints across 5 route modules. The API is the backend for the Streamlit dashboard and can also be called directly by external tools (cURL, Python, Postman).

- **OpenAPI docs (Swagger UI):** [`/docs`](http://localhost:8000/docs)
- **ReDoc:** [`/redoc`](http://localhost:8000/redoc)
- **Health:** [`GET /api/health`](#1-health-check)

---

## Table of Contents

| # | Endpoint | Method | Description |
|---|----------|--------|-------------|
| 1 | `/api/health` | GET | Server health check |
| 2 | `/api/recruit` | POST | Run full recruitment pipeline |
| 3 | `/api/feedback` | POST | Submit recruiter feedback |
| 4 | `/api/candidates` | GET | List all candidates |
| 5 | `/api/candidates` | POST | Create a new candidate |
| 6 | `/api/candidates/{id}` | GET | Get candidate by ID |
| 7 | `/api/candidates/{id}` | DELETE | Delete candidate by ID |
| 8 | `/api/upload-resume` | POST | Upload and parse a resume |
| 9 | `/api/chat` | POST | Natural language chat query |
| 10 | `/api/interview-questions` | POST | Generate interview questions |

---

## 1. Health Check

```
GET /api/health
```

Returns basic application status. Used by monitoring systems and the frontend to verify availability.

### Response `200 OK`

```json
{
  "status": "ok",
  "app": "RecruitX",
  "version": "1.0.0"
}
```

### Model

**`HealthResponse`** — defined in `api/models.py:128-139`

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"` |
| `app` | `string` | Application name from `APP_NAME` env var (default `"RecruitX"`) |
| `version` | `string` | Version from `APP_VERSION` env var (default `"1.0.0"`) |

---

## 2. Run Recruitment Pipeline

```
POST /api/recruit
```

The primary endpoint — accepts a raw job description, runs the 8-step multi-agent recruitment pipeline, and returns a ranked shortlist of candidates.

### Request Body

**`RecruitRequest`** — defined in `api/models.py:20-38`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `job_description` | `string` | Yes | — | `min_length=1` | Raw job description text |
| `top_k` | `integer` | No | `10` | `1..100` | Number of top candidates to return |

### Example Request

```json
{
  "job_description": "We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, PostgreSQL, and machine learning...",
  "top_k": 10
}
```

### Response `200 OK`

**`RecruitResponse`** — defined in `api/models.py:112-125`

```json
{
  "success": true,
  "shortlist": [
    {
      "id": 1,
      "candidate_id": 12,
      "name": "Rahul Sharma",
      "email": "rahul@example.com",
      "final_score": 87.34,
      "semantic_score": 82.1,
      "skill_score": 95.0,
      "signal_score": 78.0,
      "rank": 1,
      "explanation": "Strong match across all dimensions..."
    }
  ],
  "jd_analysis": {
    "job_title": "Senior Python Developer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Machine Learning"],
    "preferred_skills": ["Docker", "Kubernetes", "AWS"],
    "min_experience_years": 5.0,
    "education_required": "Bachelor's in Computer Science",
    "seniority_level": "Senior"
  },
  "processing_time_ms": 2345.67
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Whether the pipeline completed without errors |
| `shortlist` | `array[object]` | Ranked list of candidate entries (length = `top_k`) |
| `shortlist[].id` | `integer` | Shortlist entry database ID |
| `shortlist[].candidate_id` | `integer` | Candidate database ID |
| `shortlist[].name` | `string` | Candidate full name |
| `shortlist[].email` | `string` | Candidate email |
| `shortlist[].final_score` | `number` | Weighted final score (0–100) |
| `shortlist[].semantic_score` | `number` | FAISS semantic similarity score (0–100) |
| `shortlist[].skill_score` | `number` | Skill-matching score (0–100) |
| `shortlist[].signal_score` | `number` | Behavioral signal score (0–100) |
| `shortlist[].rank` | `integer` | Rank position (1 = best match) |
| `shortlist[].explanation` | `string` | Human-readable ranking explanation |
| `jd_analysis` | `object` | Structured job description analysis |
| `processing_time_ms` | `number` | Total pipeline execution time in milliseconds |

### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Empty or invalid `job_description` |
| `500` | Pipeline execution failure or internal error |

---

## 3. Submit Recruiter Feedback

```
POST /api/feedback
```

Record recruiter feedback (thumbs up / thumbs down) on a shortlist entry. Enables the feedback loop for future ranking improvements.

### Request Body

**`FeedbackRequest`** — defined in `api/models.py:77-88`

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `shortlist_id` | `integer` | Yes | `gt=0` | ID of the shortlist entry |
| `feedback` | `integer` | Yes | `0` or `1` | `1` = good match, `0` = bad match |

### Example Request

```json
{
  "shortlist_id": 42,
  "feedback": 1
}
```

### Response `200 OK`

```json
{
  "message": "Feedback recorded as 'good' for shortlist entry 42"
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Invalid `feedback` value (not 0 or 1) |
| `404` | `shortlist_id` not found in the database |
| `500` | Internal server error |

---

## 4. List All Candidates

```
GET /api/candidates
```

Retrieve every candidate in the database, ordered by ID ascending.

### Response `200 OK`

```json
{
  "candidates": [
    {
      "id": 1,
      "name": "Rahul Sharma",
      "email": "rahul@example.com",
      "phone": "+91-9876543210",
      "location": "Bangalore",
      "skills": "Python, FastAPI, PostgreSQL, Machine Learning, Docker",
      "experience_years": 6.0,
      "education": "B.Tech in Computer Science",
      "previous_roles": "Senior Software Engineer at TechCorp; Software Engineer at StartUp Inc",
      "profile_completeness": 85,
      "last_active_days": 2,
      "resume_path": null,
      "embedding_id": null,
      "created_at": "2026-07-12 10:30:00",
      "updated_at": "2026-07-12 10:30:00"
    }
  ]
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `500` | Database query failure |

---

## 5. Create a Candidate

```
POST /api/candidates
```

Add a new candidate manually (without resume upload). The `email` field must be unique.

### Request Body

**`CandidateCreate`** — defined in `api/models.py:41-74`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `name` | `string` | Yes | — | `min_length=1` | Candidate's full name |
| `email` | `string` | Yes | — | `min_length=1` | Unique email address |
| `skills` | `string` | Yes | — | `min_length=1` | Comma-separated skills |
| `experience_years` | `number` | No | `0` | `>= 0` | Years of work experience |
| `phone` | `string` | No | `null` | — | Phone number |
| `location` | `string` | No | `null` | — | City or location |
| `education` | `string` | No | `null` | — | Education details |
| `previous_roles` | `string` | No | `null` | — | Previous roles, semicolon-separated |
| `profile_completeness` | `integer` | No | `0` | `0..100` | Completeness percentage |
| `last_active_days` | `integer` | No | `0` | `>= 0` | Days since last activity |

### Example Request

```json
{
  "name": "Priya Patel",
  "email": "priya@example.com",
  "skills": "Python, JavaScript, React, Node.js",
  "experience_years": 4.5,
  "location": "Mumbai",
  "education": "M.Sc. in Computer Science",
  "previous_roles": "Full Stack Developer at WebCo",
  "profile_completeness": 90,
  "last_active_days": 1
}
```

### Response `200 OK`

```json
{
  "candidate": {
    "id": 51,
    "name": "Priya Patel",
    "email": "priya@example.com"
  },
  "message": "Candidate 'Priya Patel' created successfully"
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Invalid or missing required fields |
| `409` | A candidate with the same `email` already exists |
| `500` | Database insertion failure |

---

## 6. Get Candidate by ID

```
GET /api/candidates/{candidate_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `candidate_id` | `integer` | Yes | The candidate's database ID |

### Response `200 OK`

```json
{
  "candidate": {
    "id": 12,
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "phone": "+91-9876543210",
    "location": "Bangalore",
    "skills": "Python, FastAPI, PostgreSQL, Machine Learning, Docker",
    "experience_years": 6.0,
    "education": "B.Tech in Computer Science",
    "previous_roles": "Senior Software Engineer at TechCorp; Software Engineer at StartUp Inc",
    "profile_completeness": 85,
    "last_active_days": 2,
    "resume_path": null,
    "embedding_id": null,
    "created_at": "2026-07-12 10:30:00",
    "updated_at": "2026-07-12 10:30:00"
  }
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `404` | No candidate with the given `candidate_id` |
| `500` | Database query failure |

---

## 7. Delete Candidate by ID

```
DELETE /api/candidates/{candidate_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `candidate_id` | `integer` | Yes | The candidate's database ID |

### Response `200 OK`

```json
{
  "message": "Candidate with ID 12 deleted successfully"
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `404` | No candidate with the given `candidate_id` |
| `500` | Database deletion failure |

---

## 8. Upload Resume

```
POST /api/upload-resume
```

Upload a PDF or DOCX resume file. The endpoint:

1. Validates file type (`.pdf` or `.docx`) and size (max 10 MB)
2. Saves the file to the `uploads/` directory with a UUID filename
3. Extracts text from the file
4. Computes MD5 hash for duplicate detection
5. Checks for duplicate file hash or duplicate email
6. Parses text with LLM into a structured candidate profile
7. Saves candidate to the database
8. Adds candidate to the FAISS vector index

### Request

- **Content-Type:** `multipart/form-data`
- **Field:** `file` (single file upload)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | `UploadFile` | Yes | Resume file — `.pdf` or `.docx`, max 10 MB |

### Response `200 OK` — New candidate

```json
{
  "candidate": {
    "id": 52,
    "name": "Ananya Gupta",
    "email": "ananya@example.com",
    "skills": "Python, Data Science, TensorFlow",
    "experience_years": 3.0,
    "phone": "+91-9988776655",
    "location": "Delhi",
    "education": "B.Tech in Data Science",
    "previous_roles": "Data Analyst at DataCorp",
    "profile_completeness": 80,
    "last_active_days": 5,
    "resume_path": "uploads/a1b2c3d4e5f6.pdf",
    "embedding_id": 52,
    "created_at": "2026-07-12 11:00:00",
    "updated_at": "2026-07-12 11:00:00"
  },
  "message": "Resume processed successfully: Candidate 'Ananya Gupta' (ID 52) created.",
  "is_new": true
}
```

### Response `200 OK` — Duplicate file (same MD5 hash)

```json
{
  "candidate": {
    "id": 12,
    "name": "Rahul Sharma",
    ...
  },
  "message": "Duplicate resume detected — existing candidate 'Rahul Sharma' (ID 12) returned.",
  "is_new": false
}
```

### Response `409 Conflict` — Duplicate email

```json
{
  "detail": "A candidate with email 'rahul@example.com' already exists (ID 12)."
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Invalid file type (not `.pdf` or `.docx`) |
| `400` | File exceeds max size (configurable via `MAX_UPLOAD_SIZE_MB` env var, default 10 MB) |
| `400` | Resume parsing validation or runtime error |
| `409` | A candidate with the same email already exists |
| `500` | File save failure or internal processing error |

---

## 9. Chat Query

```
POST /api/chat
```

Process a natural language query from the recruiter. Uses a singleton `ChatAgent` with a two-step LLM pipeline:

1. **Intent Parser** — classifies the message into `search_candidates`, `get_candidate_details`, `count_candidates`, or `general_question`
2. **Response Generator** — converts database results into a conversational reply

Conversation history is persisted per `session_id` in the `chat_history` table.

### Request Body

**`ChatRequest`** — defined in `api/models.py:91-104`

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `message` | `string` | Yes | `min_length=1` | Natural language query |
| `session_id` | `string` | Yes | `min_length=1` | Unique session identifier for conversation continuity |

### Example Request

```json
{
  "message": "Find candidates with Python and FastAPI skills in Bangalore",
  "session_id": "session-abc-123"
}
```

### Response `200 OK`

```json
{
  "response": "I found 3 candidates with Python and FastAPI skills in Bangalore. Here they are:\n\n1. **Rahul Sharma** — 6 years exp, Bangalore\n2. **Priya Patel** — 4.5 years exp, Mumbai\n3. **Suresh Reddy** — 5 years exp, Bangalore\n\nWould you like more details on any of them?",
  "candidates": [
    {
      "id": 12,
      "name": "Rahul Sharma",
      "email": "rahul@example.com",
      "skills": "Python, FastAPI, PostgreSQL, Machine Learning, Docker",
      "experience_years": 6.0,
      "location": "Bangalore"
    }
  ],
  "session_id": "session-abc-123",
  "intent": "search_candidates"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | `string` | Conversational reply from the Chat Agent (also returned on error with a fallback message) |
| `candidates` | `array[object]` | Matching candidate records (may be empty) |
| `session_id` | `string` | Echoed session identifier |
| `intent` | `string` | Detected intent: `search_candidates`, `get_candidate_details`, `count_candidates`, `general_question`, or `error` |

### Error Handling

The chat endpoint **never returns HTTP errors** — on failure it returns HTTP `200` with:

```json
{
  "response": "I encountered a temporary issue while processing your request. Please try again in a moment.",
  "candidates": [],
  "session_id": "session-abc-123",
  "intent": "error"
}
```

---

## 10. Generate Interview Questions

```
POST /api/interview-questions
```

Generate 5–10 personalized interview questions for a candidate based on their full profile, job description, skill gap analysis, and ranking explanation. Uses a singleton `InterviewQuestionGenerator` with an LLM and 3 retry attempts.

### Request Body

**`InterviewRequest`** — defined in `api/models.py:142-169`

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `candidate_id` | `integer` | Yes | `gt=0` | Candidate's database ID |
| `candidate_name` | `string` | Yes | `min_length=1` | Candidate's full name |
| `candidate_skills` | `string` | Yes | — | Comma-separated skills |
| `candidate_experience_years` | `number` | Yes | `>= 0` | Years of experience |
| `candidate_previous_roles` | `string` | No | — | Previous roles, semicolon-separated |
| `candidate_education` | `string` | No | — | Education details |
| `job_description` | `string` | Yes | `min_length=1` | Raw job description text |
| `skill_gap_matched` | `array[string]` | No | — | Skills the candidate matched |
| `skill_gap_missing` | `array[string]` | No | — | Skills the candidate is missing |
| `skill_gap_bonus` | `array[string]` | No | — | Bonus skills the candidate has |
| `explanation` | `string` | No | — | Orchestrator's ranking explanation |

### Example Request

```json
{
  "candidate_id": 12,
  "candidate_name": "Rahul Sharma",
  "candidate_skills": "Python, FastAPI, PostgreSQL, Machine Learning, Docker",
  "candidate_experience_years": 6.0,
  "candidate_previous_roles": "Senior Software Engineer at TechCorp; Software Engineer at StartUp Inc",
  "candidate_education": "B.Tech in Computer Science",
  "job_description": "We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, PostgreSQL, and machine learning...",
  "skill_gap_matched": ["Python", "FastAPI", "PostgreSQL", "Machine Learning"],
  "skill_gap_missing": ["Kubernetes", "AWS"],
  "skill_gap_bonus": ["Docker"],
  "explanation": "Strong semantic match (82/100), excellent skill overlap (95/100), good seniority fit."
}
```

### Response `200 OK`

**`InterviewResponse`** — defined in `api/models.py:172-181`

```json
{
  "candidate_id": 12,
  "questions": [
    "Your experience includes migrating a monolith to microservices with FastAPI. Walk me through the architecture decisions and how you handled inter-service communication.",
    "You have PostgreSQL experience — describe a complex query optimization you performed and the performance gain achieved.",
    "We need someone who can mentor junior engineers. Describe a time you helped a team member level up their technical skills.",
    "How have you applied machine learning models in production, and what monitoring did you put in place?",
    "You listed Docker but not Kubernetes. What's your experience with container orchestration at scale?"
  ]
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Empty or invalid input fields |
| `500` | LLM generation failure after 3 retries, or internal error |

---

## Common Behaviours

### CORS

All origins are allowed (`Access-Control-Allow-Origin: *`). The API also allows all methods (`*`), headers (`*`), and credentials. This is configured for development with the Streamlit frontend (runs on a different port). Restrict in production.

### Authentication

No authentication or API keys are required. All endpoints are publicly accessible.

### Rate Limiting

No rate limiting is implemented.

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error description"
}
```

HTTP status codes used: `400`, `404`, `409`, `500`.

### Database Connection Lifecycle

Every request that touches the database opens a connection via `get_db_connection()` and closes it in a `finally` block. This pattern is used in all route handlers.

---

## Pipeline Architecture (Sequence Diagrams)

### Recruitment Pipeline (`POST /api/recruit`)

```
Recruiter         FastAPI         Orchestrator        JD Analyst        FAISS         Scoring Engine     DB
    |                |                  |                  |               |                |              |
    |--- POST ------->|                  |                  |               |                |              |
    |   /api/recruit  |                  |                  |               |                |              |
    |                 |-- Orchestrator-->|                  |               |                |              |
    |                 |                  |-- analyze JD --->|               |                |              |
    |                 |                  |<-- parsed JD ----|               |                |              |
    |                 |                  |-- save JD --------------------------->----------->| (job_descriptions)
    |                 |                  |-- semantic search -->|             |                |              |
    |                 |                  |<-- candidate IDs ---|             |                |              |
    |                 |                  |-- fetch candidates --------------------------------->|              |
    |                 |                  |<-- candidate data ----------------------------------|              |
    |                 |                  |-- score candidates ------------->|                  |              |
    |                 |                  |-- save shortlist ----------------------------------->| (shortlists)
    |                 |<-- results ------|                  |               |                |              |
    |<-- 200 OK ------|                  |                  |               |                |              |
```

### Resume Upload (`POST /api/upload-resume`)

```
Recruiter         FastAPI         ResumeParser        LLM           DB          FAISS
    |                |                |                |             |             |
    |--- POST ------->|                |                |             |             |
    |  /api/upload-   |                |                |             |             |
    |  resume         |-- parse ------>|                |             |             |
    |                 |                |-- extract ---->| (text)      |             |
    |                 |                |-- MD5 hash --->|             |             |
    |                 |                |-- check dup ---|------------>|             |
    |                 |                |-- LLM parse ---|---->|       |             |
    |                 |                |<-- profile ----|<----|       |             |
    |                 |                |-- save candidate ---------->|             |
    |                 |                |-- add embedding --------------------------->|
    |                 |<-- result -----|                |             |             |
    |<-- 200/409 -----|                |                |             |             |
```

### Chat Query (`POST /api/chat`)

```
Recruiter         FastAPI         ChatAgent           LLM           DB
    |                |                |                |             |
    |--- POST ------->|                |                |             |
    |  /api/chat      |-- process ---->|                |             |
    |                 |                |-- get history ------------->|
    |                 |                |-- intent parse -->|         |
    |                 |                |-- search DB --------------->|
    |                 |                |-- generate rsp --->|        |
    |                 |                |-- save user msg ----------->|
    |                 |                |-- save asst msg ----------->|
    |                 |<-- result -----|                |             |
    |<-- 200 OK ------|                |                |             |
```

---

## Workflow Examples

### Full Recruitment Cycle

```bash
# 1. Health check
curl http://localhost:8000/api/health

# 2. Upload resumes (repeat for each candidate)
curl -X POST http://localhost:8000/api/upload-resume \
  -F "file=@resumes/rahul_sharma.pdf"

# 3. Run recruitment pipeline
curl -X POST http://localhost:8000/api/recruit \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Looking for a Senior Python Developer...",
    "top_k": 5
  }'

# 4. Submit feedback on results
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"shortlist_id": 1, "feedback": 1}'

# 5. Generate interview questions for top candidate
curl -X POST http://localhost:8000/api/interview-questions \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 12,
    "candidate_name": "Rahul Sharma",
    "candidate_skills": "Python, FastAPI, PostgreSQL",
    "candidate_experience_years": 6.0,
    "job_description": "Looking for a Senior Python Developer...",
    "skill_gap_matched": ["Python", "FastAPI"],
    "skill_gap_missing": ["Kubernetes"],
    "skill_gap_bonus": ["Docker"],
    "explanation": "Strong match"
  }'
```

### Using Python (requests)

```python
import requests

BASE = "http://localhost:8000"

# Health check
r = requests.get(f"{BASE}/api/health")
print(r.json())

# Upload resume
with open("resume.pdf", "rb") as f:
    r = requests.post(f"{BASE}/api/upload-resume", files={"file": f})
    print(r.json())

# Run recruitment pipeline
r = requests.post(f"{BASE}/api/recruit", json={
    "job_description": "Senior Python Developer...",
    "top_k": 5,
})
print(r.json())
```

### Using Postman

1. Import the OpenAPI schema from `http://localhost:8000/openapi.json`
2. Use the `Body` tab: select `raw` / `JSON` for JSON endpoints
3. For resume upload: select `form-data`, key=`file` (type=File)
4. All endpoints are under `localhost:8000`

---

## Error Recovery

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `POST /api/recruit` returns `500` | LLM API key missing or quota exhausted | Check `OPENROUTER_API_KEY` in `.env` |
| `POST /api/upload-resume` returns `400` | File exceeds 10 MB | Increase `MAX_UPLOAD_SIZE_MB` in `.env` |
| `POST /api/candidates` returns `409` | Duplicate email | Use `GET /api/candidates` to find existing |
| Chat returns `intent: "error"` | LLM or database failure | Check logs; the endpoint always returns 200 |
| All requests return `500` | Database not initialized | Run `python database/db_setup.py` |
| `POST /api/interview-questions` returns `500` | LLM failure after 3 retries | Check OpenRouter status and API key |

---

## OpenAPI / Swagger

The API exposes two interactive documentation UIs powered by FastAPI:

- **Swagger UI:** [`/docs`](http://localhost:8000/docs)
- **ReDoc:** [`/redoc`](http://localhost:8000/redoc)
- **Raw OpenAPI JSON:** [`/openapi.json`](http://localhost:8000/openapi.json)

The Swagger UI supports "Try it out" for every endpoint including file uploads.

---

## Post-Processing Scoring Formula

Each shortlist entry's `final_score` is computed as:

```
final_score = (semantic_score × 0.50) + (skill_score × 0.30) + (signal_score × 0.20)
```

Where:
- **`semantic_score`** — FAISS cosine similarity (embedding-based semantic match between JD and candidate profile)
- **`skill_score`** — Jaccard-style overlap score between required/preferred skills and candidate skills
- **`signal_score`** — Behavioral signal derived from profile completeness, recency, role seniority, and education alignment

Weights are hardcoded in `scoring/scoring_engine.py` and are not yet configurable via API request parameters.

---

## Verification Checklist

| # | Item | Status |
|---|------|--------|
| 1 | All 10 endpoints documented | ✅ |
| 2 | Request/response models match `api/models.py` exactly | ✅ |
| 3 | HTTP methods and paths match route decorators | ✅ |
| 4 | Error status codes match implementations | ✅ |
| 5 | `InterviewResponse.questions` is `List[str]` | ✅ |
| 6 | `RecruitResponse.shortlist` is `List[Dict[str, Any]]` | ✅ |
| 7 | `POST /api/chat` returns `intent: "error"` on failure (not HTTP error) | ✅ |
| 8 | Resume upload max size documented as configurable via env var | ✅ |
| 9 | Feedback values documented as 0/1 | ✅ |
| 10 | No undocumented endpoints exist | ✅ |
| 11 | No real endpoints omitted | ✅ |
| 12 | Session ID required for chat | ✅ |
| 13 | Candidate ID required as path parameter for GET/DELETE | ✅ |
| 14 | Scoring weights match `scoring_engine.py` | ✅ |
| 15 | Pipeline sequence diagram matches `orchestrator.py` flow | ✅ |
