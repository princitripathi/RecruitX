"""
api/models.py — Pydantic Request/Response Models for RecruitX API

Defines all Pydantic models used for request validation and response
serialization across the RecruitX REST API endpoints.

These models follow the API specification in the Master Guide (line 422).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# Request Models
# ============================================================


class RecruitRequest(BaseModel):
    """
    Request body for POST /api/recruit.

    Attributes:
        job_description: Raw job description text from the recruiter.
        top_k: Number of top candidates to return (default: 10).
    """
    job_description: str = Field(
        ...,
        min_length=1,
        description="Raw job description text from the recruiter",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of top candidates to return",
    )


class CandidateCreate(BaseModel):
    """
    Request body for POST /api/candidates.

    Attributes:
        name: Candidate's full name.
        email: Unique email address.
        skills: Comma-separated skills string.
        experience_years: Years of work experience.
        phone: Phone number (optional).
        location: City/location (optional).
        education: Education details (optional).
        previous_roles: Previous job roles, semicolon-separated (optional).
        profile_completeness: Completeness percentage 0-100.
        last_active_days: Days since last activity.
    """
    name: str = Field(..., min_length=1, description="Candidate's full name")
    email: str = Field(..., min_length=1, description="Unique email address")
    skills: str = Field(..., min_length=1, description="Comma-separated skills")
    experience_years: float = Field(
        default=0.0, ge=0, description="Years of work experience"
    )
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City/location")
    education: Optional[str] = Field(None, description="Education details")
    previous_roles: Optional[str] = Field(
        None, description="Previous roles, semicolon-separated"
    )
    profile_completeness: int = Field(
        default=0, ge=0, le=100, description="Completeness percentage 0-100"
    )
    last_active_days: int = Field(
        default=0, ge=0, description="Days since last activity"
    )


class FeedbackRequest(BaseModel):
    """
    Request body for POST /api/feedback.

    Attributes:
        shortlist_id: ID of the shortlist entry to provide feedback on.
        feedback: 1 = good match (thumbs up), 0 = bad match (thumbs down).
    """
    shortlist_id: int = Field(..., gt=0, description="Shortlist entry ID")
    feedback: int = Field(
        ..., ge=0, le=1, description="1 = good match, 0 = bad match"
    )


class ChatRequest(BaseModel):
    """
    Request body for POST /api/chat.

    Attributes:
        message: Natural language query from the recruiter.
        session_id: Unique session identifier for conversation continuity.
    """
    message: str = Field(
        ..., min_length=1, description="Natural language query"
    )
    session_id: str = Field(
        ..., min_length=1, description="Session identifier"
    )


# ============================================================
# Response Models
# ============================================================


class RecruitResponse(BaseModel):
    """
    Response body for POST /api/recruit.

    Attributes:
        success: Whether the pipeline completed successfully.
        shortlist: Ranked list of candidate entries with scores.
        jd_analysis: Structured JD analysis from JD Analyst Agent.
        processing_time_ms: Total pipeline execution time in milliseconds.
    """
    success: bool
    shortlist: List[Dict[str, Any]]
    jd_analysis: Dict[str, Any]
    processing_time_ms: float


class HealthResponse(BaseModel):
    """
    Response body for GET /api/health.

    Attributes:
        status: Server health status ("ok").
        app: Application name.
        version: Application version.
    """
    status: str
    app: str
    version: str
