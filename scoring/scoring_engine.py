"""
scoring/scoring_engine.py — Weighted Scoring Engine for RecruitX

This module implements the core scoring formula:
    Final Score = (Semantic Score x 0.50) + (Skill Score x 0.30) + (Signal Score x 0.20)

The ScoringEngine class calculates skill match scores and weighted final scores
for candidates based on job description requirements.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Weight constants for the final score formula
WEIGHT_SEMANTIC = 0.50
WEIGHT_SKILL = 0.30
WEIGHT_SIGNAL = 0.20

# Weight constants for the skill score sub-formula
WEIGHT_REQUIRED_SKILLS = 0.70
WEIGHT_PREFERRED_SKILLS = 0.30


class ScoringEngine:
    """
    Engine that calculates candidate scores using the weighted scoring formula.

    Combines semantic similarity (from FAISS), skill matching (keyword overlap),
    and behavioral signals (from SignalAnalyzerAgent) into a single final score.
    """

    def __init__(self):
        """Initialize the Scoring Engine."""
        logger.info("Initializing ScoringEngine")

    def calculate_skill_score(
        self,
        candidate_skills: List[str],
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
    ) -> float:
        """
        Calculate the skill matching score for a candidate against JD requirements.

        Formula:
            Skill Score = (Required Skills Match x 0.70) + (Preferred Skills Match x 0.30)

        Args:
            candidate_skills: List of skills the candidate possesses.
            required_skills: List of skills required by the job description (optional).
            preferred_skills: List of skills preferred by the job description (optional).

        Returns:
            Skill score out of 100, rounded to 2 decimal places.
        """
        # Normalize all skills to lowercase set for case-insensitive matching
        candidate_set = {s.strip().lower() for s in candidate_skills if s and s.strip()}

        # --- Required Skills Match ---
        if required_skills:
            required_set = {s.strip().lower() for s in required_skills if s and s.strip()}
            total_required = len(required_set)
            if total_required > 0:
                matched_required = len(candidate_set & required_set)
                required_match_score = (matched_required / total_required) * 100.0
            else:
                # No required skills specified means nothing to miss
                required_match_score = 100.0
        else:
            required_match_score = 100.0

        # --- Preferred Skills Match ---
        if preferred_skills:
            preferred_set = {s.strip().lower() for s in preferred_skills if s and s.strip()}
            total_preferred = len(preferred_set)
            if total_preferred > 0:
                matched_preferred = len(candidate_set & preferred_set)
                preferred_match_score = (matched_preferred / total_preferred) * 100.0
            else:
                preferred_match_score = 100.0
        else:
            preferred_match_score = 100.0

        # Weighted skill score
        skill_score = (
            (required_match_score * WEIGHT_REQUIRED_SKILLS) +
            (preferred_match_score * WEIGHT_PREFERRED_SKILLS)
        )

        skill_score = round(skill_score, 2)

        logger.debug(
            "SkillScore: required=%d/%d (%.1f%%), preferred=%d/%d (%.1f%%) -> final=%.2f",
            matched_required if required_skills and total_required > 0 else 0,
            total_required if required_skills and total_required > 0 else 0,
            required_match_score,
            matched_preferred if preferred_skills and total_preferred > 0 else 0,
            total_preferred if preferred_skills and total_preferred > 0 else 0,
            preferred_match_score,
            skill_score,
        )

        return skill_score

    def calculate_final_score(
        self,
        semantic_score: float,
        skill_score: float,
        signal_score: float,
    ) -> float:
        """
        Calculate the weighted final score for a candidate.

        Formula:
            Final Score = (Semantic Score x 0.50) + (Skill Score x 0.30) + (Signal Score x 0.20)

        Args:
            semantic_score: Semantic similarity score from FAISS (0-100).
            skill_score: Skill matching score (0-100).
            signal_score: Behavioral signal score (0-100).

        Returns:
            Weighted final score out of 100, rounded to 2 decimal places.
        """
        final_score = (
            (semantic_score * WEIGHT_SEMANTIC) +
            (skill_score * WEIGHT_SKILL) +
            (signal_score * WEIGHT_SIGNAL)
        )

        final_score = round(final_score, 2)

        logger.debug(
            "FinalScore: semantic=%.2f, skill=%.2f, signal=%.2f -> final=%.2f",
            semantic_score, skill_score, signal_score, final_score,
        )

        return final_score
