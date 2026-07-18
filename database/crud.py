"""
database/crud.py — CRUD Operations for RecruitX

This module provides Create, Read, Update, Delete functions for
all database tables. Every function takes a sqlite3.Connection
as the first argument, so the caller controls the connection lifecycle.

Usage:
    from database.db_setup import get_db_connection
    from database.crud import get_all_candidates, add_candidate

    conn = get_db_connection()
    candidates = get_all_candidates(conn)
    conn.close()
"""

import logging
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# CANDIDATES — CRUD Operations
# ============================================================

def get_all_candidates(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Fetch all candidates from the database.

    Args:
        conn: Active SQLite connection

    Returns:
        List of candidate dictionaries with all columns
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY id")
    rows = cursor.fetchall()

    # Convert sqlite3.Row objects to plain dictionaries
    return [dict(row) for row in rows]


def get_candidate_by_id(conn: sqlite3.Connection, candidate_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single candidate by their ID.

    Args:
        conn: Active SQLite connection
        candidate_id: The candidate's ID

    Returns:
        Candidate dictionary, or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = cursor.fetchone()

    return dict(row) if row else None


def get_candidate_by_email(conn: sqlite3.Connection, email: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single candidate by their email address.

    Args:
        conn: Active SQLite connection
        email: The candidate's email

    Returns:
        Candidate dictionary, or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE email = ?", (email,))
    row = cursor.fetchone()

    return dict(row) if row else None


def get_candidates_by_ids(conn: sqlite3.Connection, candidate_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Fetch multiple candidates by a list of IDs.

    This is used by the orchestrator to fetch details for
    candidates returned by FAISS semantic search.

    Args:
        conn: Active SQLite connection
        candidate_ids: List of candidate IDs to fetch

    Returns:
        List of candidate dictionaries (in the order of IDs provided)
    """
    if not candidate_ids:
        return []

    # Build parameterized query with correct number of placeholders
    placeholders = ",".join(["?"] * len(candidate_ids))
    query = f"SELECT * FROM candidates WHERE id IN ({placeholders})"

    cursor = conn.cursor()
    cursor.execute(query, candidate_ids)
    rows = cursor.fetchall()

    # Convert to dicts and maintain the order of input IDs
    candidates_map = {dict(row)["id"]: dict(row) for row in rows}
    return [candidates_map[cid] for cid in candidate_ids if cid in candidates_map]


def add_candidate(
    conn: sqlite3.Connection,
    name: str,
    email: str,
    skills: str,
    experience_years: float,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    education: Optional[str] = None,
    previous_roles: Optional[str] = None,
    profile_completeness: int = 0,
    last_active_days: int = 0,
    resume_path: Optional[str] = None,
) -> int:
    """
    Insert a new candidate into the database.

    Args:
        conn: Active SQLite connection
        name: Candidate's full name
        email: Unique email address
        skills: Comma-separated skills string
        experience_years: Years of work experience
        phone: Phone number (optional)
        location: City/location (optional)
        education: Education details (optional)
        previous_roles: Previous job roles, semicolon-separated (optional)
        profile_completeness: Completeness percentage 0-100
        last_active_days: Days since last activity
        resume_path: Path to uploaded resume file (optional)

    Returns:
        The ID of the newly inserted candidate

    Raises:
        sqlite3.IntegrityError: If email already exists
    """
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO candidates (
                name, email, phone, location, skills,
                experience_years, education, previous_roles,
                profile_completeness, last_active_days, resume_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name, email, phone, location, skills,
                experience_years, education, previous_roles,
                profile_completeness, last_active_days, resume_path,
            )
        )
        conn.commit()
        new_id = cursor.lastrowid
        logger.info("✅ Added candidate '%s' with ID %d", name, new_id)
        return new_id

    except sqlite3.IntegrityError as e:
        logger.error("❌ Duplicate email '%s': %s", email, str(e))
        raise


def update_candidate(
    conn: sqlite3.Connection,
    candidate_id: int,
    **fields: Any,
) -> bool:
    """
    Update specific fields of a candidate.

    Only the fields you pass in **fields will be updated.
    Example: update_candidate(conn, 1, skills="Python,SQL", location="Mumbai")

    Args:
        conn: Active SQLite connection
        candidate_id: ID of the candidate to update
        **fields: Keyword arguments for columns to update

    Returns:
        True if candidate was found and updated, False if not found
    """
    if not fields:
        logger.warning("No fields provided for update")
        return False

    # Only allow updating known columns (prevent SQL injection)
    allowed_columns = {
        "name", "email", "phone", "location", "skills",
        "experience_years", "education", "previous_roles",
        "profile_completeness", "last_active_days", "resume_path",
        "embedding_id",
    }

    # Filter out any unknown fields
    valid_fields = {k: v for k, v in fields.items() if k in allowed_columns}
    if not valid_fields:
        logger.warning("No valid fields provided for update")
        return False

    # Build SET clause dynamically: "name = ?, skills = ?"
    set_clause = ", ".join([f"{col} = ?" for col in valid_fields.keys()])
    # Always update the updated_at timestamp
    set_clause += ", updated_at = CURRENT_TIMESTAMP"

    values = list(valid_fields.values()) + [candidate_id]

    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE candidates SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()

    if cursor.rowcount > 0:
        logger.info("✅ Updated candidate ID %d: %s", candidate_id, list(valid_fields.keys()))
        return True
    else:
        logger.warning("⚠️ Candidate ID %d not found for update", candidate_id)
        return False


def delete_candidate(conn: sqlite3.Connection, candidate_id: int) -> bool:
    """
    Delete a candidate from the database.

    Args:
        conn: Active SQLite connection
        candidate_id: ID of the candidate to delete

    Returns:
        True if candidate was found and deleted, False if not found
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()

    if cursor.rowcount > 0:
        logger.info("✅ Deleted candidate ID %d", candidate_id)
        return True
    else:
        logger.warning("⚠️ Candidate ID %d not found for deletion", candidate_id)
        return False


def search_candidates(
    conn: sqlite3.Connection,
    skills: Optional[str] = None,
    location: Optional[str] = None,
    min_experience: Optional[float] = None,
    max_experience: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Search candidates with optional filters.

    All filters are optional. If none are provided, returns all candidates.

    Args:
        conn: Active SQLite connection
        skills: Comma-separated skills to search for (uses LIKE matching)
        location: City name to filter by
        min_experience: Minimum years of experience
        max_experience: Maximum years of experience

    Returns:
        List of matching candidate dictionaries
    """
    query = "SELECT * FROM candidates WHERE 1=1"
    params: List[Any] = []

    # Add skill filter (case-insensitive LIKE for each skill)
    if skills:
        skill_list = [s.strip() for s in skills.split(",")]
        for skill in skill_list:
            query += " AND LOWER(skills) LIKE ?"
            params.append(f"%{skill.lower()}%")

    # Add location filter
    if location:
        query += " AND LOWER(location) LIKE ?"
        params.append(f"%{location.lower()}%")

    # Add experience range filter
    if min_experience is not None:
        query += " AND experience_years >= ?"
        params.append(min_experience)

    if max_experience is not None:
        query += " AND experience_years <= ?"
        params.append(max_experience)

    query += " ORDER BY experience_years DESC"

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [dict(row) for row in rows]


# ============================================================
# JOB DESCRIPTIONS — CRUD Operations
# ============================================================

def add_job_description(
    conn: sqlite3.Connection,
    title: str,
    raw_text: str,
    required_skills: Optional[str] = None,
    preferred_skills: Optional[str] = None,
    min_experience: float = 0,
    education_required: Optional[str] = None,
    seniority_level: Optional[str] = None,
) -> int:
    """
    Insert a new job description into the database.

    Called by the orchestrator after the JD Analyst parses a raw JD.

    Args:
        conn: Active SQLite connection
        title: Job title extracted from JD
        raw_text: Original raw JD text from recruiter
        required_skills: Comma-separated required skills (from JD analysis)
        preferred_skills: Comma-separated preferred skills (from JD analysis)
        min_experience: Minimum years required
        education_required: Education requirement string
        seniority_level: Junior/Mid/Senior/Lead

    Returns:
        The ID of the newly inserted job description
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO job_descriptions (
            title, raw_text, required_skills, preferred_skills,
            min_experience, education_required, seniority_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title, raw_text, required_skills, preferred_skills,
            min_experience, education_required, seniority_level,
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    logger.info("✅ Added job description '%s' with ID %d", title, new_id)
    return new_id


# ============================================================
# SHORTLISTS — CRUD Operations
# ============================================================


def add_shortlist_batch(
    conn: sqlite3.Connection,
    entries: List[Dict[str, Any]],
) -> int:
    """
    Insert multiple shortlist entries in a single transaction.

    Args:
        conn: Active SQLite connection
        entries: List of dicts, each with keys:
                 jd_id, candidate_id, final_score, semantic_score,
                 skill_score, signal_score, rank, explanation

    Returns:
        Number of entries inserted
    """
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO shortlists (
            jd_id, candidate_id, final_score, semantic_score,
            skill_score, signal_score, rank, explanation
        ) VALUES (
            :jd_id, :candidate_id, :final_score, :semantic_score,
            :skill_score, :signal_score, :rank, :explanation
        )
        """,
        entries
    )
    conn.commit()
    count = cursor.rowcount
    logger.info("✅ Inserted %d shortlist entries", count)
    return count


def get_shortlist_by_jd(
    conn: sqlite3.Connection, jd_id: int
) -> List[Dict[str, Any]]:
    """
    Get the full shortlist for a job description, ranked by position.

    Args:
        conn: Active SQLite connection
        jd_id: ID of the job description

    Returns:
        List of shortlist entries ordered by rank (best first)
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.*, c.name, c.email, c.skills, c.experience_years, c.location
        FROM shortlists s
        JOIN candidates c ON s.candidate_id = c.id
        WHERE s.jd_id = ?
        ORDER BY s.rank ASC
        """,
        (jd_id,)
    )
    rows = cursor.fetchall()

    return [dict(row) for row in rows]


def update_recruiter_feedback(
    conn: sqlite3.Connection,
    shortlist_id: int,
    feedback: int,
) -> bool:
    """
    Record recruiter feedback for a shortlisted candidate.

    Args:
        conn: Active SQLite connection
        shortlist_id: ID of the shortlist entry
        feedback: 1 = good match (thumbs up), 0 = bad match (thumbs down)

    Returns:
        True if updated successfully, False if entry not found
    """
    if feedback not in (0, 1):
        logger.error("❌ Invalid feedback value: %s (must be 0 or 1)", feedback)
        raise ValueError("Feedback must be 0 (bad) or 1 (good)")

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE shortlists SET recruiter_feedback = ? WHERE id = ?",
        (feedback, shortlist_id)
    )
    conn.commit()

    if cursor.rowcount > 0:
        label = "👍 Good" if feedback == 1 else "👎 Bad"
        logger.info("✅ Feedback recorded for shortlist ID %d: %s", shortlist_id, label)
        return True
    else:
        logger.warning("⚠️ Shortlist ID %d not found", shortlist_id)
        return False


# ============================================================
# RESUMES — CRUD Operations
# ============================================================

def add_resume(
    conn: sqlite3.Connection,
    file_name: str,
    file_path: str,
    file_hash: str,
    candidate_id: Optional[int] = None,
    parsed_text: Optional[str] = None,
) -> int:
    """
    Insert a resume record into the database.

    Uses file_hash (MD5) for duplicate detection — if a resume with the
    same hash already exists, a sqlite3.IntegrityError is raised.

    Args:
        conn: Active SQLite connection
        file_name: Original file name (e.g., "resume_rahul.pdf")
        file_path: Path where file is stored on disk
        file_hash: MD5 hash of the file for deduplication
        candidate_id: ID of the candidate this resume belongs to (optional)
        parsed_text: Extracted text content from the resume (optional)

    Returns:
        The ID of the newly inserted resume record

    Raises:
        sqlite3.IntegrityError: If file_hash already exists (duplicate resume)
    """
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO resumes (
                candidate_id, file_name, file_path, file_hash, parsed_text
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, file_name, file_path, file_hash, parsed_text)
        )
        conn.commit()
        new_id = cursor.lastrowid
        logger.info("✅ Added resume '%s' with ID %d", file_name, new_id)
        return new_id

    except sqlite3.IntegrityError:
        logger.warning("⚠️ Duplicate resume detected (hash: %s)", file_hash)
        raise


def get_resume_by_hash(
    conn: sqlite3.Connection, file_hash: str
) -> Optional[Dict[str, Any]]:
    """
    Check if a resume with the given hash already exists.

    Used for duplicate detection before saving a new upload.

    Args:
        conn: Active SQLite connection
        file_hash: MD5 hash of the file

    Returns:
        Resume dictionary if found, None otherwise
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resumes WHERE file_hash = ?", (file_hash,))
    row = cursor.fetchone()

    return dict(row) if row else None


# ============================================================
# CHAT HISTORY — CRUD Operations
# ============================================================

def add_chat_message(
    conn: sqlite3.Connection,
    session_id: str,
    role: str,
    message: str,
) -> int:
    """
    Insert a chat message into the conversation history.

    Args:
        conn: Active SQLite connection
        session_id: Unique session identifier for the conversation
        role: Either 'user' or 'assistant'
        message: The message text

    Returns:
        The ID of the newly inserted message
    """
    if role not in ("user", "assistant"):
        raise ValueError(f"Invalid role '{role}'. Must be 'user' or 'assistant'.")

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_history (session_id, role, message)
        VALUES (?, ?, ?)
        """,
        (session_id, role, message)
    )
    conn.commit()
    return cursor.lastrowid


def get_chat_history(
    conn: sqlite3.Connection,
    session_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch chat messages for a given session, ordered chronologically.

    Args:
        conn: Active SQLite connection
        session_id: The session to fetch history for
        limit: Maximum number of messages to return (default 50)

    Returns:
        List of message dictionaries with role, message, created_at
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM chat_history
        WHERE session_id = ?
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (session_id, limit)
    )
    rows = cursor.fetchall()

    return [dict(row) for row in rows]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def get_candidate_count(conn: sqlite3.Connection) -> int:
    """
    Get the total number of candidates in the database.

    Args:
        conn: Active SQLite connection

    Returns:
        Total candidate count
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM candidates")
    return cursor.fetchone()[0]
