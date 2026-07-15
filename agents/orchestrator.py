"""
agents/orchestrator.py — Recruitment Orchestrator Agent for RecruitX

This is the master coordinator that connects all previously built agents
into a single recruitment pipeline. Given a raw job description text,
it orchestrates the following sequence:

    1. JD Analyst Agent        → parse JD into structured requirements
    2. Candidate Ranker Agent  → semantic search → top K candidate IDs
    3. Database lookup         → fetch full candidate profiles
    4. Signal Analyzer Agent   → behavioral signal scores per candidate
    5. Scoring Engine          → skill scores + final weighted scores
    6. Skill Gap Analyzer      → matched/missing/bonus skills per candidate
    7. Database persistence    → save JD and shortlist entries
    8. Final response          → sorted shortlist with explanations

Usage:
    from agents.orchestrator import RecruitmentOrchestrator

    orchestrator = RecruitmentOrchestrator()
    result = orchestrator.run_recruitment_pipeline(
        jd_text="We are looking for a Senior Python Developer...",
        top_k=10,
    )
    # result == {
    #     "success": True,
    #     "shortlist": [...],
    #     "jd_analysis": {...},
    #     "processing_time_ms": 1234.56,
    # }
"""

import gc
import logging
import time
from typing import Any, Dict, List, Optional

from agents.candidate_ranker import CandidateRankerAgent
from agents.jd_analyst import JDAnalysis, JDAnalystAgent
from agents.signal_analyzer import SignalAnalyzerAgent
from database.crud import (
    add_job_description,
    add_shortlist_batch,
    get_candidates_by_ids,
)
from database.db_setup import get_db_connection
from scoring.scoring_engine import ScoringEngine
from scoring.skill_gap import SkillGapAnalyzer

logger = logging.getLogger(__name__)


class RecruitmentOrchestrator:
    """
    Master coordinator that runs the complete recruitment pipeline.

    Orchestrates all sub-agents in sequence, manages database persistence,
    and constructs the final ranked shortlist with human-readable explanations.

    Accepts optional pre-configured agents for dependency injection
    (useful for testing). If not provided, creates real instances.
    """

    def __init__(
        self,
        jd_analyst: Optional[JDAnalystAgent] = None,
        candidate_ranker: Optional[CandidateRankerAgent] = None,
        signal_analyzer: Optional[SignalAnalyzerAgent] = None,
        scoring_engine: Optional[ScoringEngine] = None,
        skill_gap_analyzer: Optional[SkillGapAnalyzer] = None,
    ) -> None:
        """
        Initialize the Recruitment Orchestrator with all sub-agents.

        Args:
            jd_analyst: JDAnalystAgent instance (created automatically if None).
            candidate_ranker: CandidateRankerAgent instance (created automatically if None).
            signal_analyzer: SignalAnalyzerAgent instance (created automatically if None).
            scoring_engine: ScoringEngine instance (created automatically if None).
            skill_gap_analyzer: SkillGapAnalyzer instance (created automatically if None).
        """
        self.jd_analyst = jd_analyst or JDAnalystAgent()
        self.candidate_ranker = candidate_ranker or CandidateRankerAgent()
        self.signal_analyzer = signal_analyzer or SignalAnalyzerAgent()
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.skill_gap_analyzer = skill_gap_analyzer or SkillGapAnalyzer()

        logger.info("Initialized RecruitmentOrchestrator with all 5 agents")

    def run_recruitment_pipeline(
        self,
        jd_text: str,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute the complete recruitment pipeline from JD to ranked shortlist.

        Pipeline steps:
            1. JD Analyst      — parse JD into structured requirements
            2. Candidate Ranker — find top K candidates via FAISS semantic search
            3. Database lookup  — fetch full candidate profiles from SQLite
            4. Signal Analyzer  — compute behavioral signal scores per candidate
            5. Scoring Engine   — compute skill scores and weighted final scores
            6. Skill Gap Analyzer — identify matched/missing/bonus skills
            7. Persist results  — save JD and shortlist to SQLite
            8. Build response   — construct final ranked shortlist with explanations

        Args:
            jd_text: Raw job description text from the recruiter.
            top_k: Number of top candidates to return (default: 10).

        Returns:
            Dictionary with:
                - success (bool): True if pipeline completed.
                - shortlist (list): Ranked candidate entries with scores and skill gaps.
                - jd_analysis (dict): Structured JD analysis from the JD Analyst.
                - processing_time_ms (float): Total execution time in milliseconds.

        Raises:
            ValueError: If jd_text is empty or top_k is less than 1.
            RuntimeError: If a critical sub-module fails irrecoverably.
        """
        if not jd_text or not isinstance(jd_text, str) or not jd_text.strip():
            logger.error("Empty or invalid job description text provided")
            raise ValueError("Job description text must be a non-empty string")

        if not isinstance(top_k, int) or top_k < 1:
            logger.error("Invalid top_k value: %s", top_k)
            raise ValueError("top_k must be a positive integer")

        start_time = time.time()

        # ---------------------------------------------------------------
        # Step 1: JD Analyst — Parse raw JD into structured requirements
        # ---------------------------------------------------------------
        logger.info("Step 1/8: Analyzing job description...")
        try:
            jd_analysis: JDAnalysis = self.jd_analyst.analyze(jd_text)
        except ValueError as e:
            logger.error("JD Analyst validation error: %s", str(e))
            raise
        except Exception as e:
            logger.error("JD Analyst failed: %s", str(e))
            raise RuntimeError(f"JD Analyst failed: {e}")

        gc.collect()

        # ---------------------------------------------------------------
        # Step 2: Candidate Ranker — Semantic search via FAISS
        # ---------------------------------------------------------------
        logger.info("Step 2/8: Searching for candidates (top_k=%d)...", top_k)
        try:
            ranked_candidates: List[tuple] = self.candidate_ranker.rank_candidates(
                jd_analysis.search_query, top_k=top_k
            )
        except FileNotFoundError as e:
            logger.error("FAISS index not found: %s", str(e))
            raise RuntimeError(f"FAISS index not found: {e}")
        except Exception as e:
            logger.error("Candidate ranking failed: %s", str(e))
            raise RuntimeError(f"Candidate ranking failed: {e}")

        gc.collect()

        if not ranked_candidates:
            elapsed = (time.time() - start_time) * 1000
            logger.info("No candidates found matching the job description")
            return self._build_response(jd_analysis, [], round(elapsed, 2))

        # ---------------------------------------------------------------
        # Step 3: Database lookup — Fetch candidate details from SQLite
        # ---------------------------------------------------------------
        logger.info("Step 3/8: Fetching %d candidate profiles...", len(ranked_candidates))
        candidate_ids = [cid for cid, _ in ranked_candidates]
        conn = get_db_connection()
        try:
            db_candidates = get_candidates_by_ids(conn, candidate_ids)
        except Exception as e:
            logger.error("Database lookup failed: %s", str(e))
            raise RuntimeError(f"Database lookup failed: {e}")
        finally:
            conn.close()

        candidate_map = {c["id"]: c for c in db_candidates}

        # ---------------------------------------------------------------
        # Steps 4-6: Per-candidate processing
        #   Signal Analyzer → Scoring Engine → Skill Gap Analyzer
        # ---------------------------------------------------------------
        logger.info("Steps 4-6/8: Scoring %d candidates...", len(ranked_candidates))
        entries = self._process_candidates(ranked_candidates, candidate_map, jd_analysis)

        gc.collect()

        if not entries:
            elapsed = (time.time() - start_time) * 1000
            logger.warning("No candidates could be processed (all skipped)")
            return self._build_response(jd_analysis, [], round(elapsed, 2))

        # Sort by final_score descending and assign ranks
        entries.sort(key=lambda e: e["final_score"], reverse=True)
        for i, entry in enumerate(entries):
            entry["rank"] = i + 1
            entry["explanation"] = self._build_explanation(entry, i + 1)

        # ---------------------------------------------------------------
        # Step 7: Persist results to database
        # ---------------------------------------------------------------
        logger.info("Step 7/8: Persisting results to database...")
        self._persist_results(jd_analysis, jd_text, entries)

        # ---------------------------------------------------------------
        # Step 8: Build and return final response
        # ---------------------------------------------------------------
        elapsed = (time.time() - start_time) * 1000
        result = self._build_response(jd_analysis, entries, round(elapsed, 2))

        logger.info(
            "Pipeline complete: %d candidates ranked in %.0f ms",
            len(entries), elapsed,
        )

        return result

    def _process_candidates(
        self,
        ranked_candidates: List[tuple],
        candidate_map: Dict[int, Dict[str, Any]],
        jd_analysis: JDAnalysis,
    ) -> List[Dict[str, Any]]:
        """
        Process each ranked candidate through Signal Analyzer, Scoring Engine,
        and Skill Gap Analyzer.

        Args:
            ranked_candidates: List of (candidate_id, semantic_score) tuples.
            candidate_map: Dict mapping candidate_id to candidate dict from DB.
            jd_analysis: Structured JD analysis from the JD Analyst.

        Returns:
            List of processed candidate entries with all scores and skill gaps.
        """
        entries: List[Dict[str, Any]] = []

        for cid, semantic_score in ranked_candidates:
            candidate = candidate_map.get(cid)
            if candidate is None:
                logger.warning(
                    "Candidate ID %d not found in database, skipping", cid
                )
                continue

            # Parse comma-separated skills string into list
            skills_raw: str = candidate.get("skills", "") or ""
            candidate_skills = [
                s.strip() for s in skills_raw.split(",") if s.strip()
            ]

            # ---- Step 4: Signal Analyzer ----
            try:
                signal_result = self.signal_analyzer.analyze_signals(
                    candidate, jd_analysis.min_experience_years
                )
            except Exception as e:
                logger.error(
                    "Signal analysis failed for candidate ID %d: %s", cid, str(e)
                )
                signal_result = {
                    "signal_score": 0.0,
                    "recency_score": 0.0,
                    "completeness_score": 0.0,
                    "experience_match": 0.0,
                }

            # ---- Step 5: Scoring Engine ----
            try:
                skill_score = self.scoring_engine.calculate_skill_score(
                    candidate_skills,
                    jd_analysis.required_skills,
                    jd_analysis.preferred_skills,
                )

                final_score = self.scoring_engine.calculate_final_score(
                    semantic_score,
                    skill_score,
                    signal_result["signal_score"],
                )
            except Exception as e:
                logger.error(
                    "Scoring failed for candidate ID %d: %s", cid, str(e)
                )
                skill_score = 0.0
                final_score = 0.0

            # ---- Step 6: Skill Gap Analyzer ----
            try:
                skill_gap = self.skill_gap_analyzer.analyze(
                    candidate_skills,
                    jd_analysis.required_skills,
                    jd_analysis.preferred_skills,
                )
            except Exception as e:
                logger.error(
                    "Skill gap analysis failed for candidate ID %d: %s",
                    cid, str(e),
                )
                skill_gap = {"matched": [], "missing": [], "bonus": []}

            entry: Dict[str, Any] = {
                "candidate_id": cid,
                "semantic_score": semantic_score,
                "skill_score": skill_score,
                "signal_score": signal_result["signal_score"],
                "final_score": final_score,
                "recency_score": signal_result["recency_score"],
                "completeness_score": signal_result["completeness_score"],
                "experience_match": signal_result["experience_match"],
                "skill_gap": skill_gap,
                "rank": 0,
                "explanation": "",
            }
            entries.append(entry)

        return entries

    def _build_explanation(
        self, entry: Dict[str, Any], rank: int
    ) -> str:
        """
        Generate a human-readable explanation for a candidate's ranking.

        Args:
            entry: Processed candidate entry with scores and skill gap.
            rank: Final rank position (1 = best).

        Returns:
            Human-readable explanation string.
        """
        sg = entry["skill_gap"]
        matched_count = len(sg.get("matched", []))
        missing_count = len(sg.get("missing", []))

        parts = [f"Rank #{rank}."]

        # Skill match summary
        if matched_count > 0 and missing_count > 0:
            parts.append(
                f"Matched {matched_count} skill(s), missing {missing_count} skill(s)."
            )
        elif matched_count > 0:
            parts.append(f"Matched all {matched_count} required/preferred skill(s).")
        elif missing_count > 0:
            parts.append(f"Missing {missing_count} required skill(s).")

        # Semantic fit
        parts.append(f"Semantic fit: {entry['semantic_score']:.1f}/100.")

        # Recency
        recency = entry.get("recency_score", 0)
        if recency >= 80:
            parts.append("Recently active.")
        elif recency >= 40:
            parts.append("Moderately active.")

        # Experience match
        exp_match = entry.get("experience_match", 0)
        if exp_match >= 80:
            parts.append("Experience meets requirements.")
        elif exp_match >= 40:
            parts.append("Partially meets experience requirements.")

        return " ".join(parts)

    def _persist_results(
        self,
        jd_analysis: JDAnalysis,
        jd_text: str,
        entries: List[Dict[str, Any]],
    ) -> None:
        """
        Save the job description and shortlist entries to the database.

        Args:
            jd_analysis: Structured JD analysis.
            jd_text: Original raw JD text.
            entries: Processed candidate entries with all scores.

        Raises:
            RuntimeError: If database persistence fails.
        """
        conn = get_db_connection()
        try:
            # Convert JD analysis lists to comma-separated strings for DB
            required_str: Optional[str] = None
            if jd_analysis.required_skills:
                required_str = ", ".join(jd_analysis.required_skills)

            preferred_str: Optional[str] = None
            if jd_analysis.preferred_skills:
                preferred_str = ", ".join(jd_analysis.preferred_skills)

            jd_id = add_job_description(
                conn,
                title=jd_analysis.role_summary[:100]
                if jd_analysis.role_summary
                else "Unknown Role",
                raw_text=jd_text,
                required_skills=required_str,
                preferred_skills=preferred_str,
                min_experience=jd_analysis.min_experience_years,
                education_required=jd_analysis.education_required,
                seniority_level=jd_analysis.seniority_level,
            )

            # Build batch entries for shortlist table
            batch: List[Dict[str, Any]] = []
            for e in entries:
                batch.append({
                    "jd_id": jd_id,
                    "candidate_id": e["candidate_id"],
                    "final_score": e["final_score"],
                    "semantic_score": e["semantic_score"],
                    "skill_score": e["skill_score"],
                    "signal_score": e["signal_score"],
                    "rank": e["rank"],
                    "explanation": e["explanation"],
                })

            insert_count = add_shortlist_batch(conn, batch)
            logger.info(
                "Persisted JD ID %d with %d shortlist entries",
                jd_id, insert_count,
            )

        except Exception as e:
            logger.error("Failed to persist results to database: %s", str(e))
            raise RuntimeError(f"Database persistence failed: {e}")
        finally:
            conn.close()

    def _build_response(
        self,
        jd_analysis: JDAnalysis,
        entries: List[Dict[str, Any]],
        elapsed_ms: float,
    ) -> Dict[str, Any]:
        """
        Construct the final API-friendly response dictionary.

        Args:
            jd_analysis: Structured JD analysis.
            entries: Processed candidate entries (may be empty).
            elapsed_ms: Total pipeline execution time in milliseconds.

        Returns:
            Response dictionary matching the API specification.
        """
        shortlist: List[Dict[str, Any]] = []
        for e in entries:
            shortlist_entry: Dict[str, Any] = {
                "rank": e["rank"],
                "candidate_id": e["candidate_id"],
                "final_score": e["final_score"],
                "semantic_score": e["semantic_score"],
                "skill_score": e["skill_score"],
                "signal_score": e["signal_score"],
                "explanation": e["explanation"],
                "skill_gap": e["skill_gap"],
            }
            shortlist.append(shortlist_entry)

        # Convert Pydantic model to dict for JSON serialization
        jd_dict = jd_analysis.model_dump()

        return {
            "success": True,
            "shortlist": shortlist,
            "jd_analysis": jd_dict,
            "processing_time_ms": elapsed_ms,
        }
