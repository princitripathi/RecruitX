"""
agents/signal_analyzer.py — Behavioral Signal Analyzer Agent for RecruitX

This agent evaluates candidate metadata (profile completeness, last active days,
and years of experience) to compute sub-scores and a final weighted Signal Score.
It is purely algorithmic and does not use LLMs.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Constants for Signal Scoring weights
WEIGHT_COMPLETENESS = 0.40
WEIGHT_RECENCY = 0.40
WEIGHT_EXPERIENCE_MATCH = 0.20


class SignalAnalyzerAgent:
    """
    Agent responsible for analyzing behavioral signals from candidate profiles
    (completeness, recency, experience ratio) and generating a weighted signal score.
    """

    def __init__(self):
        """Initialize the Signal Analyzer Agent."""
        logger.info("Initializing SignalAnalyzerAgent")

    def calculate_recency_score(self, last_active_days: int) -> float:
        """
        Calculate the Recency Score based on activity days threshold.

        Args:
            last_active_days: Number of days since candidate's last activity.

        Returns:
            Recency score out of 100.
        """
        if last_active_days is None:
            # Default to a high number representing inactive
            last_active_days = 999

        if last_active_days <= 7:
            return 100.0
        elif last_active_days <= 30:
            return 80.0
        elif last_active_days <= 90:
            return 60.0
        elif last_active_days <= 180:
            return 40.0
        elif last_active_days <= 365:
            return 20.0
        else:
            return 5.0

    def calculate_experience_match(self, candidate_experience: float, required_experience: float) -> float:
        """
        Calculate the Experience Match score based on candidate vs required experience.

        Args:
            candidate_experience: Candidate's years of experience.
            required_experience: Required years of experience from JD.

        Returns:
            Experience match score out of 100.
        """
        # Safe checks
        if candidate_experience is None or candidate_experience < 0:
            candidate_experience = 0.0

        if required_experience is None or required_experience <= 0:
            # If no experience is required, any candidate satisfies the requirement
            return 100.0

        ratio = candidate_experience / required_experience

        if ratio >= 1.0:
            return 100.0
        elif ratio >= 0.8:
            return 80.0
        elif ratio >= 0.6:
            return 60.0
        else:
            return 30.0

    def analyze_signals(self, candidate: Dict[str, Any], required_experience: float) -> Dict[str, Any]:
        """
        Analyze candidate metadata signals to calculate sub-scores and a final Signal Score.

        Args:
            candidate: Dictionary containing candidate profile data.
            required_experience: Required years of experience from job description.

        Returns:
            Dictionary containing final signal score and its constituent sub-scores:
            {
                "signal_score": float,
                "recency_score": float,
                "completeness_score": float,
                "experience_match": float
            }
        """
        try:
            # Extract inputs with safe defaults
            completeness = float(candidate.get("profile_completeness", 0) or 0)
            last_active = candidate.get("last_active_days", 999)
            experience = float(candidate.get("experience_years", 0) or 0)

            # 1. Profile Completeness Score (0-100)
            completeness_score = min(max(completeness, 0.0), 100.0)

            # 2. Recency Score
            recency_score = self.calculate_recency_score(last_active)

            # 3. Experience Match Score
            exp_match_score = self.calculate_experience_match(experience, required_experience)

            # 4. Final Weighted Signal Score
            final_signal_score = (
                (completeness_score * WEIGHT_COMPLETENESS) +
                (recency_score * WEIGHT_RECENCY) +
                (exp_match_score * WEIGHT_EXPERIENCE_MATCH)
            )

            # Round final score to 2 decimal places for clean representation
            final_signal_score = round(final_signal_score, 2)

            logger.debug(
                "Candidate ID %s: Completeness=%.1f, Recency=%.1f, ExpMatch=%.1f -> SignalScore=%.2f",
                candidate.get("id"), completeness_score, recency_score, exp_match_score, final_signal_score
            )

            return {
                "signal_score": final_signal_score,
                "recency_score": recency_score,
                "completeness_score": completeness_score,
                "experience_match": exp_match_score
            }

        except Exception as e:
            logger.error("Error analyzing signals for candidate: %s", str(e), exc_info=True)
            # Safe fallback response in case of any unhandled exception
            return {
                "signal_score": 0.0,
                "recency_score": 0.0,
                "completeness_score": 0.0,
                "experience_match": 0.0
            }
