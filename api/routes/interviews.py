"""
api/routes/interviews.py — Interview Question Generator API Endpoint for RecruitX

Endpoints:
    POST /api/interview-questions — Generate personalized interview questions
        for a candidate based on their profile, job description, skill gap
        analysis, and ranking explanation.

This endpoint is the primary interface between the recruiter dashboard and
the InterviewQuestionGenerator. It remains stateless — every call regenerates
questions from scratch.
"""

import logging

from fastapi import APIRouter, HTTPException

from api.models import InterviewRequest, InterviewResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy singleton — created on first use to avoid blocking FastAPI startup
_generator = None


def _get_generator():
    global _generator
    if _generator is None:
        from utils.interview_generator import InterviewQuestionGenerator
        _generator = InterviewQuestionGenerator()
    return _generator


@router.post("/api/interview-questions", response_model=InterviewResponse)
def generate_interview_questions(request: InterviewRequest):
    """
    Generate personalized interview questions for a candidate.

    Accepts the candidate's full profile, job description, skill gap analysis,
    and ranking explanation. Uses an LLM to generate 5-10 targeted questions
    that probe missing skills, verify claimed experience, and assess role fit.

    Args:
        request: InterviewRequest with candidate info, JD, skill gaps, and explanation.

    Returns:
        InterviewResponse with candidate_id and list of question strings.

    Raises:
        HTTPException 400: If inputs are invalid or the generator fails.
        HTTPException 500: If an unexpected error occurs.
    """
    try:
        # Build candidate_info dict from the request fields
        candidate_info = {
            "name": request.candidate_name,
            "skills": request.candidate_skills,
            "experience_years": request.candidate_experience_years,
            "previous_roles": request.candidate_previous_roles,
            "education": request.candidate_education,
        }

        skill_gap = {
            "matched": request.skill_gap_matched,
            "missing": request.skill_gap_missing,
            "bonus": request.skill_gap_bonus,
        }

        logger.info(
            "Generating interview questions for candidate ID %d (%s)",
            request.candidate_id,
            request.candidate_name,
        )

        gen = _get_generator()
        result = gen.generate(
            candidate_info=candidate_info,
            job_description=request.job_description,
            skill_gap=skill_gap,
            explanation=request.explanation,
        )

        logger.info(
            "Generated %d interview questions for candidate ID %d",
            len(result.questions),
            request.candidate_id,
        )

        return InterviewResponse(
            candidate_id=request.candidate_id,
            questions=result.questions,
        )

    except ValueError as e:
        logger.error(
            "Invalid interview question request for candidate ID %d: %s",
            request.candidate_id,
            str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(
            "Interview question generation failed for candidate ID %d: %s",
            request.candidate_id,
            str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(
            "Unexpected error generating interview questions for candidate ID %d: %s",
            request.candidate_id,
            str(e),
        )
        raise HTTPException(status_code=500, detail="Internal server error")
