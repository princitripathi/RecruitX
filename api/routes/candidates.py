"""
api/routes/candidates.py — Candidate Management API Endpoints for RecruitX

Endpoints:
    GET    /api/candidates        — List all candidates
    POST   /api/candidates        — Add a new candidate
    GET    /api/candidates/{id}   — Get a single candidate by ID
    DELETE /api/candidates/{id}   — Delete a candidate by ID

All endpoints use the CRUD functions from database/crud.py and follow the
try/finally pattern for safe database connection management.
"""

import logging

from fastapi import APIRouter, HTTPException

from api.models import CandidateCreate
from database import crud
from database.db_setup import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/candidates")
def list_candidates():
    """
    Retrieve all candidates from the database.

    Returns:
        Dict with "candidates" key containing a list of candidate dicts.
    """
    conn = get_db_connection()
    try:
        candidates = crud.get_all_candidates(conn)
        logger.info("Retrieved %d candidates", len(candidates))
        return {"candidates": candidates}
    except Exception as e:
        logger.error("Failed to list candidates: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve candidates")
    finally:
        conn.close()


@router.post("/api/candidates")
def create_candidate(request: CandidateCreate):
    """
    Add a new candidate to the database.

    Args:
        request: CandidateCreate with candidate profile data.

    Returns:
        Dict with the new candidate's ID and a success message.

    Raises:
        HTTPException 409: If a candidate with the same email already exists.
    """
    conn = get_db_connection()
    try:
        new_id = crud.add_candidate(
            conn,
            name=request.name,
            email=request.email,
            skills=request.skills,
            experience_years=request.experience_years,
            phone=request.phone,
            location=request.location,
            education=request.education,
            previous_roles=request.previous_roles,
            profile_completeness=request.profile_completeness,
            last_active_days=request.last_active_days,
        )
        logger.info("Created candidate '%s' with ID %d", request.name, new_id)
        return {
            "candidate": {"id": new_id, "name": request.name, "email": request.email},
            "message": f"Candidate '{request.name}' created successfully",
        }

    except ValueError as e:
        logger.error("Invalid candidate data: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg or "integrity" in error_msg:
            logger.warning("Duplicate email attempt: %s", request.email)
            raise HTTPException(
                status_code=409,
                detail=f"A candidate with email '{request.email}' already exists",
            )
        logger.error("Failed to create candidate: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to create candidate")
    finally:
        conn.close()


@router.get("/api/candidates/{candidate_id}")
def get_candidate(candidate_id: int):
    """
    Retrieve a single candidate by their ID.

    Args:
        candidate_id: The candidate's database ID.

    Returns:
        Dict with the candidate's data.

    Raises:
        HTTPException 404: If the candidate is not found.
    """
    conn = get_db_connection()
    try:
        candidate = crud.get_candidate_by_id(conn, candidate_id)

        if candidate is None:
            logger.warning("Candidate ID %d not found", candidate_id)
            raise HTTPException(
                status_code=404,
                detail=f"Candidate with ID {candidate_id} not found",
            )

        logger.info("Retrieved candidate ID %d", candidate_id)
        return {"candidate": candidate}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get candidate ID %d: %s", candidate_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate")
    finally:
        conn.close()


@router.delete("/api/candidates/{candidate_id}")
def remove_candidate(candidate_id: int):
    """
    Delete a candidate by their ID.

    Args:
        candidate_id: The candidate's database ID.

    Returns:
        Dict with a success message.

    Raises:
        HTTPException 404: If the candidate is not found.
    """
    conn = get_db_connection()
    try:
        deleted = crud.delete_candidate(conn, candidate_id)

        if not deleted:
            logger.warning("Candidate ID %d not found for deletion", candidate_id)
            raise HTTPException(
                status_code=404,
                detail=f"Candidate with ID {candidate_id} not found",
            )

        logger.info("Deleted candidate ID %d", candidate_id)
        return {"message": f"Candidate with ID {candidate_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete candidate ID %d: %s", candidate_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to delete candidate")
    finally:
        conn.close()
