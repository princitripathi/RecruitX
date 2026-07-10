"""
tests/test_api.py — Tests for the RecruitX FastAPI Backend

Tests all API endpoints using FastAPI's TestClient with mocked
database and orchestrator dependencies.

Endpoints tested:
    GET    /api/health
    POST   /api/recruit
    POST   /api/feedback
    GET    /api/candidates
    POST   /api/candidates
    GET    /api/candidates/{id}
    DELETE /api/candidates/{id}
    POST   /api/upload-resume
    POST   /api/chat
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ===================================================================
# Health Check
# ===================================================================


class TestHealthCheck:
    """GET /api/health"""

    def test_health_returns_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "RecruitX"
        assert data["version"] == "1.0.0"

    def test_health_response_structure(self):
        response = client.get("/api/health")
        data = response.json()
        assert set(data.keys()) == {"status", "app", "version"}


# ===================================================================
# Recruitment Pipeline
# ===================================================================


class TestRecruitEndpoint:
    """POST /api/recruit"""

    SAMPLE_JD = "We are looking for a Senior Python Developer with 5+ years experience."

    @patch("api.routes.recruitment.RecruitmentOrchestrator")
    def test_recruit_success(self, mock_orchestrator_class):
        mock_instance = MagicMock()
        mock_instance.run_recruitment_pipeline.return_value = {
            "success": True,
            "shortlist": [
                {
                    "rank": 1,
                    "candidate_id": 1,
                    "final_score": 95.2,
                    "semantic_score": 92.0,
                    "skill_score": 100.0,
                    "signal_score": 96.0,
                    "explanation": "Rank #1. Matched all skills.",
                    "skill_gap": {
                        "matched": ["Python", "FastAPI"],
                        "missing": [],
                        "bonus": ["SQL"],
                    },
                }
            ],
            "jd_analysis": {
                "required_skills": ["Python", "FastAPI"],
                "preferred_skills": ["AWS"],
                "min_experience_years": 3.0,
                "education_required": "B.Tech",
                "seniority_level": "Senior",
                "role_summary": "Senior Python Developer",
                "search_query": "Python FastAPI AWS",
            },
            "processing_time_ms": 1250.5,
        }
        mock_orchestrator_class.return_value = mock_instance

        response = client.post(
            "/api/recruit",
            json={"job_description": self.SAMPLE_JD, "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["shortlist"]) == 1
        assert data["shortlist"][0]["rank"] == 1
        assert data["shortlist"][0]["final_score"] == 95.2
        assert data["processing_time_ms"] == 1250.5
        assert "required_skills" in data["jd_analysis"]

    def test_recruit_empty_jd_returns_422(self):
        response = client.post(
            "/api/recruit",
            json={"job_description": ""},
        )
        # Pydantic min_length validation catches this -> 422
        assert response.status_code == 422

    def test_recruit_missing_jd_returns_422(self):
        response = client.post(
            "/api/recruit",
            json={},
        )
        assert response.status_code == 422

    @patch("api.routes.recruitment.RecruitmentOrchestrator")
    def test_recruit_orchestrator_value_error(self, mock_orchestrator_class):
        mock_instance = MagicMock()
        mock_instance.run_recruitment_pipeline.side_effect = ValueError(
            "Job description text must be a non-empty string"
        )
        mock_orchestrator_class.return_value = mock_instance

        response = client.post(
            "/api/recruit",
            json={"job_description": self.SAMPLE_JD},
        )
        assert response.status_code == 400
        assert "non-empty" in response.json()["detail"]

    @patch("api.routes.recruitment.RecruitmentOrchestrator")
    def test_recruit_orchestrator_runtime_error(self, mock_orchestrator_class):
        mock_instance = MagicMock()
        mock_instance.run_recruitment_pipeline.side_effect = RuntimeError(
            "FAISS index not found"
        )
        mock_orchestrator_class.return_value = mock_instance

        response = client.post(
            "/api/recruit",
            json={"job_description": self.SAMPLE_JD},
        )
        assert response.status_code == 500
        assert "FAISS" in response.json()["detail"]

    @patch("api.routes.recruitment.RecruitmentOrchestrator")
    def test_recruit_top_k_defaults_to_10(self, mock_orchestrator_class):
        mock_instance = MagicMock()
        mock_instance.run_recruitment_pipeline.return_value = {
            "success": True,
            "shortlist": [],
            "jd_analysis": {},
            "processing_time_ms": 0.0,
        }
        mock_orchestrator_class.return_value = mock_instance

        client.post(
            "/api/recruit",
            json={"job_description": self.SAMPLE_JD},
        )

        # Verify default top_k=10 was used
        call_kwargs = mock_instance.run_recruitment_pipeline.call_args[1]
        assert call_kwargs["top_k"] == 10


# ===================================================================
# Feedback
# ===================================================================


class TestFeedbackEndpoint:
    """POST /api/feedback"""

    @patch("api.routes.recruitment.get_db_connection")
    @patch("api.routes.recruitment.crud.update_recruiter_feedback")
    def test_feedback_success(self, mock_update, mock_conn):
        mock_update.return_value = True

        response = client.post(
            "/api/feedback",
            json={"shortlist_id": 1, "feedback": 1},
        )

        assert response.status_code == 200
        assert "Feedback recorded" in response.json()["message"]

    @patch("api.routes.recruitment.get_db_connection")
    @patch("api.routes.recruitment.crud.update_recruiter_feedback")
    def test_feedback_not_found(self, mock_update, mock_conn):
        mock_update.return_value = False

        response = client.post(
            "/api/feedback",
            json={"shortlist_id": 999, "feedback": 1},
        )

        assert response.status_code == 404

    def test_feedback_invalid_value_returns_422(self):
        # feedback=5 violates Pydantic's le=1 constraint -> 422
        response = client.post(
            "/api/feedback",
            json={"shortlist_id": 1, "feedback": 5},
        )

        assert response.status_code == 422

    def test_feedback_missing_fields_returns_422(self):
        response = client.post(
            "/api/feedback",
            json={},
        )
        assert response.status_code == 422


# ===================================================================
# Candidates CRUD
# ===================================================================


class TestListCandidates:
    """GET /api/candidates"""

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.get_all_candidates")
    def test_list_candidates(self, mock_get_all, mock_conn):
        mock_get_all.return_value = [
            {"id": 1, "name": "Rahul", "email": "rahul@test.com", "skills": "Python"},
            {"id": 2, "name": "Priya", "email": "priya@test.com", "skills": "Java"},
        ]

        response = client.get("/api/candidates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["candidates"]) == 2
        assert data["candidates"][0]["name"] == "Rahul"

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.get_all_candidates")
    def test_list_candidates_empty(self, mock_get_all, mock_conn):
        mock_get_all.return_value = []

        response = client.get("/api/candidates")
        assert response.status_code == 200
        assert response.json()["candidates"] == []


class TestCreateCandidate:
    """POST /api/candidates"""

    VALID_CANDIDATE = {
        "name": "Test User",
        "email": "test@example.com",
        "skills": "Python, SQL",
        "experience_years": 3.0,
    }

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.add_candidate")
    def test_create_candidate_success(self, mock_add, mock_conn):
        mock_add.return_value = 42

        response = client.post(
            "/api/candidates",
            json=self.VALID_CANDIDATE,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["candidate"]["id"] == 42
        assert data["candidate"]["name"] == "Test User"
        assert "created successfully" in data["message"]

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.add_candidate")
    def test_create_duplicate_email(self, mock_add, mock_conn):
        mock_add.side_effect = Exception("UNIQUE constraint failed")

        response = client.post(
            "/api/candidates",
            json=self.VALID_CANDIDATE,
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_missing_name_returns_422(self):
        response = client.post(
            "/api/candidates",
            json={"email": "test@test.com", "skills": "Python"},
        )
        assert response.status_code == 422

    def test_create_empty_name_returns_422(self):
        response = client.post(
            "/api/candidates",
            json={"name": "", "email": "test@test.com", "skills": "Python", "experience_years": 0},
        )
        assert response.status_code == 422


class TestGetCandidate:
    """GET /api/candidates/{id}"""

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.get_candidate_by_id")
    def test_get_candidate_found(self, mock_get, mock_conn):
        mock_get.return_value = {"id": 1, "name": "Rahul", "email": "rahul@test.com"}

        response = client.get("/api/candidates/1")
        assert response.status_code == 200
        assert response.json()["candidate"]["name"] == "Rahul"

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.get_candidate_by_id")
    def test_get_candidate_not_found(self, mock_get, mock_conn):
        mock_get.return_value = None

        response = client.get("/api/candidates/999")
        assert response.status_code == 404


class TestDeleteCandidate:
    """DELETE /api/candidates/{id}"""

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.delete_candidate")
    def test_delete_candidate_found(self, mock_delete, mock_conn):
        mock_delete.return_value = True

        response = client.delete("/api/candidates/1")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    @patch("api.routes.candidates.get_db_connection")
    @patch("api.routes.candidates.crud.delete_candidate")
    def test_delete_candidate_not_found(self, mock_delete, mock_conn):
        mock_delete.return_value = False

        response = client.delete("/api/candidates/999")
        assert response.status_code == 404


# ===================================================================
# Resume Upload (Phase 13 — AI Resume Parser)
# ===================================================================


class TestResumeUpload:
    """POST /api/upload-resume"""

    def test_upload_invalid_file_type(self):
        response = client.post(
            "/api/upload-resume",
            files={"file": ("resume.txt", b"fake content", "text/plain")},
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    @patch("api.routes.resumes.ResumeParser")
    def test_upload_valid_pdf(self, mock_parser_class):
        mock_instance = MagicMock()
        mock_instance.process_resume.return_value = {
            "candidate": {
                "id": 1,
                "name": "Rahul Sharma",
                "email": "rahul@test.com",
                "skills": "Python, SQL",
                "experience_years": 5.0,
                "location": "Bangalore",
            },
            "message": "Resume parsed successfully — candidate 'Rahul Sharma' (ID 1) created.",
            "is_new": True,
        }
        mock_parser_class.return_value = mock_instance

        response = client.post(
            "/api/upload-resume",
            files={"file": ("resume.pdf", b"%PDF-1.4 fake pdf content", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_new"] is True
        assert data["candidate"] is not None
        assert data["candidate"]["name"] == "Rahul Sharma"

    @patch("api.routes.resumes.ResumeParser")
    def test_upload_valid_docx(self, mock_parser_class):
        mock_instance = MagicMock()
        mock_instance.process_resume.return_value = {
            "candidate": {
                "id": 2,
                "name": "Priya Singh",
                "email": "priya@test.com",
                "skills": "Java, Spring",
                "experience_years": 3.0,
            },
            "message": "Resume parsed successfully — candidate 'Priya Singh' (ID 2) created.",
            "is_new": True,
        }
        mock_parser_class.return_value = mock_instance

        response = client.post(
            "/api/upload-resume",
            files={"file": ("resume.docx", b"fake docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["candidate"]["name"] == "Priya Singh"

    @patch("api.routes.resumes.ResumeParser")
    def test_upload_duplicate_resume(self, mock_parser_class):
        mock_instance = MagicMock()
        mock_instance.process_resume.return_value = {
            "candidate": {"id": 5, "name": "Existing User", "email": "existing@test.com"},
            "message": "Duplicate resume detected — existing candidate 'Existing User' (ID 5) returned.",
            "is_new": False,
        }
        mock_parser_class.return_value = mock_instance

        response = client.post(
            "/api/upload-resume",
            files={"file": ("resume.pdf", b"same content same hash", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_new"] is False
        assert "Duplicate" in data["message"]

    @patch("api.routes.resumes.ResumeParser")
    def test_upload_parser_error(self, mock_parser_class):
        mock_instance = MagicMock()
        mock_instance.process_resume.side_effect = ValueError("Invalid email format")
        mock_parser_class.return_value = mock_instance

        response = client.post(
            "/api/upload-resume",
            files={"file": ("resume.pdf", b"some content", "application/pdf")},
        )
        assert response.status_code == 400
        assert "Invalid email" in response.json()["detail"]


# ===================================================================
# Chat (Stub)
# ===================================================================


class TestChatEndpoint:
    """POST /api/chat"""

    def test_chat_returns_placeholder(self):
        response = client.post(
            "/api/chat",
            json={
                "message": "Show Python developers",
                "session_id": "test-session-123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "under construction" in data["response"].lower()
        assert data["candidates"] == []

    def test_chat_missing_message_returns_422(self):
        response = client.post(
            "/api/chat",
            json={"session_id": "test-session"},
        )
        assert response.status_code == 422


# ===================================================================
# CORS Headers
# ===================================================================


class TestCORS:
    """Verify CORS headers are present on all responses."""

    def test_cors_headers_present(self):
        # CORSMiddleware adds headers when Origin is present
        response = client.get("/api/health", headers={"Origin": "http://localhost:8501"})
        cors_header = response.headers.get("access-control-allow-origin")
        assert cors_header is not None
        assert cors_header in ("*", "http://localhost:8501")
