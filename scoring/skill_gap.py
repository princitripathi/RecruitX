"""
scoring/skill_gap.py — Skill Gap Analysis for RecruitX

This module analyzes the gap between a candidate's skills and the
skills required/preferred by a job description. It identifies:

    - Matched skills: candidate has them, JD wants them
    - Missing skills: JD requires them, candidate lacks them
    - Bonus skills: candidate has them, JD didn't ask for them

The orchestrator uses this to attach skill gap data to shortlist results,
and the dashboard displays them as color-coded tags (Feature 3 in the
Master Guide).

Usage:
    from scoring.skill_gap import SkillGapAnalyzer

    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL", "AWS"],
        required_skills=["Python", "Docker"],
        preferred_skills=["Kubernetes"],
    )
    # result == {
    #     "matched": ["Python"],
    #     "missing": ["Docker"],
    #     "bonus": ["AWS"],
    # }
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SkillGapAnalyzer:
    """
    Analyzes the gap between a candidate's skills and job description requirements.

    Performs case-insensitive, whitespace-normalized comparison
    and returns uniquely deduplicated results sorted alphabetically
    with original casing preserved.

    This is a pure algorithmic module — no LLM calls required.
    """

    def __init__(self) -> None:
        """Initialize the Skill Gap Analyzer."""
        logger.info("Initializing SkillGapAnalyzer")

    def _normalize_skills(self, skills: Optional[List[str]]) -> Dict[str, str]:
        """
        Normalize a list of skills for case-insensitive comparison.

        Strips whitespace, lowercases, and deduplicates by keeping
        the first occurrence of each skill. Returns a mapping from
        normalized form to original form so original casing can be
        preserved in the output.

        Args:
            skills: List of skill strings, or None

        Returns:
            Dict mapping lowercase-stripped key -> original value.
            Empty dict if input is None or empty.
        """
        normalized: Dict[str, str] = {}

        if not skills:
            return normalized

        for skill in skills:
            if not skill or not isinstance(skill, str):
                logger.debug("Skipping invalid skill entry: %s", repr(skill))
                continue

            key = skill.strip().lower()
            if not key:
                continue

            # Keep the first occurrence only (deduplication)
            if key not in normalized:
                normalized[key] = skill.strip()

        return normalized

    def analyze(
        self,
        candidate_skills: List[str],
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        """
        Analyze the skill gap between a candidate and a job description.

        Compares candidate skills against required and preferred skills
        using case-insensitive, whitespace-normalized matching.

        Args:
            candidate_skills: Skills the candidate possesses.
            required_skills: Skills required by the job description (optional).
            preferred_skills: Skills preferred by the job description (optional).

        Returns:
            Dictionary with three keys, each containing a sorted list of
            unique skill strings with original casing preserved:
                - matched: skills candidate has that JD requires or prefers
                - missing: skills JD requires that candidate lacks
                - bonus: skills candidate has that JD does not mention

        Raises:
            ValueError: If candidate_skills is None or not a list.
        """
        if candidate_skills is None or not isinstance(candidate_skills, list):
            logger.error("Invalid candidate_skills: must be a list")
            raise ValueError("candidate_skills must be a list")

        # Normalize all skill lists to {normalized_key: original_value} dicts
        candidate_map = self._normalize_skills(candidate_skills)
        required_map = self._normalize_skills(required_skills)
        preferred_map = self._normalize_skills(preferred_skills)

        # Build sets of normalized keys for set operations
        candidate_keys = set(candidate_map.keys())
        required_keys = set(required_map.keys())
        preferred_keys = set(preferred_map.keys())

        # Skills the JD cares about (required ∪ preferred)
        jd_keys = required_keys | preferred_keys

        # --- Matched: candidate has them, JD wants them ---
        matched_keys = candidate_keys & jd_keys

        # --- Missing: JD requires them, candidate lacks them ---
        missing_keys = required_keys - candidate_keys

        # --- Bonus: candidate has them, JD didn't ask ---
        bonus_keys = candidate_keys - jd_keys

        # Map normalized keys back to original casing, sorted alphabetically
        # Use the candidate's casing for matched and bonus
        # Use the JD's casing (required_map) for missing
        matched = sorted([candidate_map[k] for k in matched_keys])
        missing = sorted([required_map[k] for k in missing_keys])
        bonus = sorted([candidate_map[k] for k in bonus_keys])

        result: Dict[str, List[str]] = {
            "matched": matched,
            "missing": missing,
            "bonus": bonus,
        }

        logger.debug(
            "SkillGap: candidate=%d, required=%d, preferred=%d -> matched=%d, missing=%d, bonus=%d",
            len(candidate_keys),
            len(required_keys),
            len(preferred_keys),
            len(matched),
            len(missing),
            len(bonus),
        )

        return result
