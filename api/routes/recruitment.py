"""
api/routes/recruitment.py — Recruitment API Endpoints for RecruitX

Endpoints:
    POST /api/recruit   — Run the full recruitment pipeline and return ranked shortlist
    POST /api/feedback  — Submit recruiter feedback on a shortlist entry

These endpoints are the primary interface between the recruiter (via
Streamlit dashboard) and the RecruitmentOrchestrator agent.
"""

import logging

from fastapi import APIRouter, HTTPException

from api.models import FeedbackRequest, RecruitRequest, RecruitResponse
from database import crud
from database.db_setup import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/recruit", response_model=RecruitResponse)
def recruit(request: RecruitRequest):
    """
    Run the recruitment pipeline and return a ranked shortlist.

    Accepts a raw job description, analyzes it using the JD Analyst Agent,
    searches for matching candidates via FAISS semantic search, scores and
    ranks them, and returns the top K results with explanations.

    Args:
        request: RecruitRequest with job_description and optional top_k.

    Returns:
        RecruitResponse with success flag, shortlist, jd_analysis, and processing time.

    Raises:
        HTTPException 400: If the job description is empty or invalid.
        HTTPException 500: If the pipeline fails internally.
    """
    try:
        from agents.orchestrator import RecruitmentOrchestrator
        orchestrator = RecruitmentOrchestrator()
        result = orchestrator.run_recruitment_pipeline(
            jd_text=request.job_description,
            top_k=request.top_k,
        )
        logger.info(
            "Recruitment pipeline completed: %d candidates in %.0f ms",
            len(result.get("shortlist", [])),
            result.get("processing_time_ms", 0),
        )
        return RecruitResponse(**result)

    except ValueError as e:
        logger.error("Invalid recruitment request: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("Pipeline execution failed: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected recruitment error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/feedback")
def submit_feedback(request: FeedbackRequest):
    """
    Submit recruiter feedback on a shortlist entry.

    Feedback values:
        1 = good match (thumbs up)
        0 = bad match (thumbs down)

    This enables the feedback loop feature for future ranking improvements.

    Args:
        request: FeedbackRequest with shortlist_id and feedback value.

    Returns:
        Dict with success message.

    Raises:
        HTTPException 400: If feedback value is invalid.
        HTTPException 404: If shortlist entry is not found.
    """
    conn = get_db_connection()
    try:
        success = crud.update_recruiter_feedback(
            conn,
            shortlist_id=request.shortlist_id,
            feedback=request.feedback,
        )

        if not success:
            logger.warning(
                "Shortlist entry %d not found for feedback",
                request.shortlist_id,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Shortlist entry {request.shortlist_id} not found",
            )

        label = "good" if request.feedback == 1 else "bad"
        logger.info(
            "Feedback recorded for shortlist %d: %s",
            request.shortlist_id, label,
        )
        return {
            "message": f"Feedback recorded as '{label}' for shortlist entry {request.shortlist_id}",
        }

    except ValueError as e:
        logger.error("Invalid feedback value: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Feedback submission failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()
