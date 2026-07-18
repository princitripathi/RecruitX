"""
embeddings/build_index.py — Shared FAISS index utilities for RecruitX

Provides generate_candidate_text() used by both the CLI build script
(scripts/build_index.py) and the resume parser (utils/resume_parser.py).
"""


def generate_candidate_text(candidate: dict) -> str:
    """
    Generate a rich, single-string text representation of a candidate.

    Args:
        candidate: Candidate dictionary from database.

    Returns:
        A formatted string describing candidate's location, skills, experience,
        education, and previous roles.
    """
    name = candidate.get("name", "").strip()
    location = candidate.get("location", "").strip()
    skills = candidate.get("skills", "").strip()
    experience = candidate.get("experience_years", 0)
    education = candidate.get("education", "").strip()
    previous_roles = candidate.get("previous_roles")

    text_parts = []
    if name:
        text_parts.append(f"Candidate: {name}.")
    if location:
        text_parts.append(f"Location: {location}.")
    if skills:
        text_parts.append(f"Skills: {skills}.")
    if experience is not None:
        text_parts.append(f"Experience: {experience} years.")
    if education:
        text_parts.append(f"Education: {education}.")
    if previous_roles:
        roles_clean = str(previous_roles).replace(";", ",").strip()
        text_parts.append(f"Previous Roles: {roles_clean}.")

    return " ".join(text_parts)
