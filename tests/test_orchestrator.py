"""
tests/test_orchestrator.py — Tests for the Recruitment Orchestrator Agent

Tests the complete recruitment pipeline orchestration:
    - Successful end-to-end pipeline
    - Error handling (empty JD, no candidates, sub-module failures)
    - Score aggregation and ranking order
    - Skill gap attachment
    - Database persistence
    - Output structure validation
"""

from unittest.mock import MagicMock, patch

import pytest

from agents.jd_analyst import JDAnalysis
from agents.orchestrator import RecruitmentOrchestrator

# ---------------------------------------------------------------------------
# Fixtures: reusable mock data
# ---------------------------------------------------------------------------

SAMPLE_JD_TEXT = """
We are looking for a Senior Python Developer with 5+ years of experience.
Required skills: Python, FastAPI, PostgreSQL.
Preferred skills: AWS, Docker.
Education: Bachelor's in Computer Science.
"""


@pytest.fixture
def mock_jd_analysis():
    """Return a standard JDAnalysis object for testing."""
    return JDAnalysis(
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["AWS", "Docker"],
        min_experience_years=3.0,
        education_required="Bachelor's in Computer Science",
        seniority_level="Senior",
        role_summary="Senior Python Developer to build scalable applications.",
        search_query="Senior Python Developer FastAPI PostgreSQL AWS Docker",
    )


@pytest.fixture
def mock_candidate_a():
    """Candidate with strong skill match."""
    return {
        "id": 1,
        "name": "Rahul Sharma",
        "email": "rahul@example.com",
        "phone": "9876543210",
        "location": "Bangalore",
        "skills": "Python, FastAPI, PostgreSQL, AWS, Docker, SQL",
        "experience_years": 5.0,
        "education": "B.Tech CS",
        "previous_roles": "Senior Dev at TCS",
        "profile_completeness": 90,
        "last_active_days": 3,
        "resume_path": None,
        "embedding_id": 0,
    }


@pytest.fixture
def mock_candidate_b():
    """Candidate with partial skill match."""
    return {
        "id": 2,
        "name": "Priya Singh",
        "email": "priya@example.com",
        "phone": "9876543211",
        "location": "Mumbai",
        "skills": "Python, SQL, Java, Spring Boot",
        "experience_years": 3.0,
        "education": "B.Tech IT",
        "previous_roles": "Backend Dev at Infosys",
        "profile_completeness": 75,
        "last_active_days": 45,
        "resume_path": None,
        "embedding_id": 1,
    }


@pytest.fixture
def mock_candidate_c():
    """Candidate with poor skill match."""
    return {
        "id": 3,
        "name": "Amit Kumar",
        "email": "amit@example.com",
        "phone": "9876543212",
        "location": "Delhi",
        "skills": "Java, C++, MySQL",
        "experience_years": 1.0,
        "education": "BCA",
        "previous_roles": "Junior Dev at Wipro",
        "profile_completeness": 50,
        "last_active_days": 150,
        "resume_path": None,
        "embedding_id": 2,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_successful_pipeline(
    mock_jd_analysis,
    mock_candidate_a,
    mock_candidate_b,
):
    """Full end-to-end pipeline returns correct structure with scored candidates."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [
        (1, 92.0),
        (2, 75.0),
    ]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a, mock_candidate_b],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=2):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    # Check top-level structure
    assert result["success"] is True
    assert "shortlist" in result
    assert "jd_analysis" in result
    assert "processing_time_ms" in result
    assert isinstance(result["processing_time_ms"], float)
    assert result["processing_time_ms"] >= 0

    # Check jd_analysis is a dict with expected keys
    jd = result["jd_analysis"]
    assert "Python" in jd["required_skills"]
    assert jd["min_experience_years"] == 3.0
    assert jd["seniority_level"] == "Senior"

    # Check shortlist
    assert len(result["shortlist"]) == 2

    # Candidate 1 (strong match) should be ranked first
    entry_a = result["shortlist"][0]
    assert entry_a["rank"] == 1
    assert entry_a["candidate_id"] == 1

    # Candidate 1 has higher final_score than candidate 2
    assert entry_a["final_score"] > result["shortlist"][1]["final_score"]


def test_output_structure(
    mock_jd_analysis,
    mock_candidate_a,
):
    """Every shortlist entry must contain all required fields from the Master Guide."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    entry = result["shortlist"][0]

    # Required fields per Master Guide scoring spec
    assert "rank" in entry
    assert "candidate_id" in entry
    assert "final_score" in entry
    assert "semantic_score" in entry
    assert "skill_score" in entry
    assert "signal_score" in entry
    assert "explanation" in entry
    assert "skill_gap" in entry

    # Score ranges
    assert 0.0 <= entry["final_score"] <= 100.0
    assert 0.0 <= entry["semantic_score"] <= 100.0
    assert 0.0 <= entry["skill_score"] <= 100.0
    assert 0.0 <= entry["signal_score"] <= 100.0

    # Skill gap structure
    sg = entry["skill_gap"]
    assert "matched" in sg
    assert "missing" in sg
    assert "bonus" in sg
    assert isinstance(sg["matched"], list)
    assert isinstance(sg["missing"], list)
    assert isinstance(sg["bonus"], list)


def test_score_aggregation(
    mock_jd_analysis,
    mock_candidate_a,
):
    """Verify scores are calculated correctly using the weighted formula."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    entry = result["shortlist"][0]

    # Candidate A has: Python, FastAPI, PostgreSQL, AWS, Docker, SQL
    # Required: Python, FastAPI, PostgreSQL (3/3 = 100%)
    # Preferred: AWS, Docker (2/2 = 100%)
    # Skill Score = (100 * 0.70) + (100 * 0.30) = 100.0
    assert entry["skill_score"] == 100.0

    # Semantic score should be the normalized value from the ranker
    assert entry["semantic_score"] == 92.0

    # Signal score should be calculated from candidate profile
    # completeness=90, last_active=3 days, experience=5.0, required=3.0
    # recency: 3 <= 7 -> 100.0
    # experience match: 5.0/3.0 >= 1.0 -> 100.0
    # signal = (90 * 0.40) + (100 * 0.40) + (100 * 0.20) = 36 + 40 + 20 = 96.0
    assert entry["signal_score"] == 96.0

    # Final = (92.0 * 0.50) + (100.0 * 0.30) + (96.0 * 0.20)
    #       = 46.0 + 30.0 + 19.2 = 95.2
    assert entry["final_score"] == 95.2


def test_skill_gap_attachment(
    mock_jd_analysis,
    mock_candidate_a,
):
    """Skill gap analysis is correctly attached per candidate."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    sg = result["shortlist"][0]["skill_gap"]

    # Candidate has: Python, FastAPI, PostgreSQL, AWS, Docker, SQL
    # Required: Python, FastAPI, PostgreSQL
    # Preferred: AWS, Docker
    # Matched = candidate ∩ (required ∪ preferred) = all 5
    # Missing = required - candidate = none
    # Bonus = candidate - (required ∪ preferred) = SQL
    assert "Python" in sg["matched"]
    assert "FastAPI" in sg["matched"]
    assert "PostgreSQL" in sg["matched"]
    assert "AWS" in sg["matched"]
    assert "Docker" in sg["matched"]
    assert len(sg["matched"]) == 5
    assert sg["missing"] == []
    assert sg["bonus"] == ["SQL"]


def test_ranking_order(
    mock_jd_analysis,
    mock_candidate_a,
    mock_candidate_b,
    mock_candidate_c,
):
    """Candidates are ranked by final_score descending."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    # Order by semantic score (will be re-ranked by final_score)
    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [
        (1, 95.0),
        (2, 75.0),
        (3, 40.0),
    ]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a, mock_candidate_b, mock_candidate_c],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=3):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    shortlist = result["shortlist"]
    assert len(shortlist) == 3

    # Verify strictly descending by final_score
    for i in range(len(shortlist) - 1):
        assert shortlist[i]["final_score"] >= shortlist[i + 1]["final_score"]

    # Ranks should be 1, 2, 3
    assert shortlist[0]["rank"] == 1
    assert shortlist[1]["rank"] == 2
    assert shortlist[2]["rank"] == 3

    # Candidate A (best match) should be first
    assert shortlist[0]["candidate_id"] == 1


def test_empty_jd_raises_error():
    """Empty or invalid job description should raise ValueError."""
    orchestrator = RecruitmentOrchestrator(
        jd_analyst=MagicMock(),
        candidate_ranker=MagicMock(),
    )

    with pytest.raises(ValueError, match="non-empty"):
        orchestrator.run_recruitment_pipeline("")

    with pytest.raises(ValueError, match="non-empty"):
        orchestrator.run_recruitment_pipeline("   ")

    with pytest.raises(ValueError, match="non-empty"):
        orchestrator.run_recruitment_pipeline(None)  # type: ignore


def test_invalid_top_k_raises_error():
    """top_k less than 1 should raise ValueError."""
    orchestrator = RecruitmentOrchestrator(
        jd_analyst=MagicMock(),
        candidate_ranker=MagicMock(),
    )

    with pytest.raises(ValueError, match="positive integer"):
        orchestrator.run_recruitment_pipeline("Valid JD text", top_k=0)

    with pytest.raises(ValueError, match="positive integer"):
        orchestrator.run_recruitment_pipeline("Valid JD text", top_k=-5)


def test_no_candidates_found(
    mock_jd_analysis,
):
    """When ranker returns no candidates, response has empty shortlist."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = []

    orchestrator = RecruitmentOrchestrator(
        jd_analyst=mock_jd,
        candidate_ranker=mock_ranker,
    )

    result = orchestrator.run_recruitment_pipeline(SAMPLE_JD_TEXT, top_k=10)

    assert result["success"] is True
    assert result["shortlist"] == []
    assert result["processing_time_ms"] >= 0

    # JD analysis should still be present
    assert "required_skills" in result["jd_analysis"]


def test_jd_analyst_failure():
    """When JD Analyst fails, the error propagates."""
    mock_jd = MagicMock()
    mock_jd.analyze.side_effect = RuntimeError("LLM API unavailable")

    orchestrator = RecruitmentOrchestrator(
        jd_analyst=mock_jd,
        candidate_ranker=MagicMock(),
    )

    with pytest.raises(RuntimeError, match="JD Analyst failed"):
        orchestrator.run_recruitment_pipeline(SAMPLE_JD_TEXT, top_k=10)


def test_candidate_ranker_failure(
    mock_jd_analysis,
):
    """When Candidate Ranker fails, the error propagates."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.side_effect = RuntimeError("FAISS index corrupted")

    orchestrator = RecruitmentOrchestrator(
        jd_analyst=mock_jd,
        candidate_ranker=mock_ranker,
    )

    with pytest.raises(RuntimeError, match="Candidate ranking failed"):
        orchestrator.run_recruitment_pipeline(SAMPLE_JD_TEXT, top_k=10)


def test_missing_candidate_in_db(
    mock_jd_analysis,
    mock_candidate_a,
):
    """When a candidate from FAISS is not in DB, it is skipped gracefully."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    # Two candidates from FAISS, but only one in DB
    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [
        (1, 92.0),
        (999, 80.0),  # 999 does not exist in DB
    ]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    # Only 1 candidate should be in the shortlist (ID 999 was skipped)
    assert len(result["shortlist"]) == 1
    assert result["shortlist"][0]["candidate_id"] == 1


def test_database_persistence(
    mock_jd_analysis,
    mock_candidate_a,
    mock_candidate_b,
):
    """Verify that results are saved to the database."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [
        (1, 92.0),
        (2, 75.0),
    ]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a, mock_candidate_b],
        ):
            # Use real call tracking to verify persistence functions were called
            with patch(
                "agents.orchestrator.add_job_description"
            ) as mock_add_jd:
                mock_add_jd.return_value = 42
                with patch(
                    "agents.orchestrator.add_shortlist_batch"
                ) as mock_add_batch:
                    mock_add_batch.return_value = 2

                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    # Verify add_job_description was called with correct args
    mock_add_jd.assert_called_once()
    call_kwargs = mock_add_jd.call_args[1]
    assert call_kwargs["raw_text"] == SAMPLE_JD_TEXT
    assert call_kwargs["min_experience"] == 3.0
    assert call_kwargs["seniority_level"] == "Senior"

    # Verify add_shortlist_batch was called with 2 entries
    mock_add_batch.assert_called_once()
    batch_entries = mock_add_batch.call_args[0][1]
    assert len(batch_entries) == 2
    assert batch_entries[0]["jd_id"] == 42
    assert batch_entries[0]["rank"] == 1
    assert batch_entries[1]["rank"] == 2


def test_pipeline_with_single_candidate(
    mock_jd_analysis,
    mock_candidate_a,
):
    """Pipeline works correctly with a single candidate."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 85.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    assert len(result["shortlist"]) == 1
    assert result["shortlist"][0]["rank"] == 1
    assert result["shortlist"][0]["candidate_id"] == 1


def test_explanation_format(
    mock_jd_analysis,
    mock_candidate_a,
):
    """Explanation should be a non-empty human-readable string."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    explanation = result["shortlist"][0]["explanation"]
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert explanation.startswith("Rank #1.")
    assert "Semantic fit:" in explanation


def test_database_persistence_failure(
    mock_jd_analysis,
    mock_candidate_a,
):
    """When DB persistence fails, the error propagates."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch(
                "agents.orchestrator.add_job_description",
                side_effect=Exception("Disk full"),
            ):
                orchestrator = RecruitmentOrchestrator(
                    jd_analyst=mock_jd,
                    candidate_ranker=mock_ranker,
                )

                with pytest.raises(RuntimeError, match="Database persistence failed"):
                    orchestrator.run_recruitment_pipeline(SAMPLE_JD_TEXT, top_k=10)


def test_all_candidates_skipped_from_db(
    mock_jd_analysis,
):
    """When no candidates from FAISS exist in DB, result has empty shortlist."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [
        (999, 92.0),
        (888, 75.0),
    ]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=0):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    assert result["success"] is True
    assert result["shortlist"] == []


def test_dependency_injection():
    """Orchestrator uses injected agents when provided."""
    mock_jd = MagicMock()
    mock_ranker = MagicMock()
    mock_signal = MagicMock()
    mock_scoring = MagicMock()
    mock_skill = MagicMock()

    orchestrator = RecruitmentOrchestrator(
        jd_analyst=mock_jd,
        candidate_ranker=mock_ranker,
        signal_analyzer=mock_signal,
        scoring_engine=mock_scoring,
        skill_gap_analyzer=mock_skill,
    )

    assert orchestrator.jd_analyst is mock_jd
    assert orchestrator.candidate_ranker is mock_ranker
    assert orchestrator.signal_analyzer is mock_signal
    assert orchestrator.scoring_engine is mock_scoring
    assert orchestrator.skill_gap_analyzer is mock_skill


def test_signal_analyzer_failure_uses_fallback(
    mock_jd_analysis,
    mock_candidate_a,
):
    """When Signal Analyzer fails for a candidate, fallback score of 0 is used."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_signal = MagicMock()
    mock_signal.analyze_signals.side_effect = Exception("Unexpected error")

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                        signal_analyzer=mock_signal,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    entry = result["shortlist"][0]
    # Signal score should be 0 (fallback) but other scores should still work
    assert entry["signal_score"] == 0.0
    # Semantic score still comes through
    assert entry["semantic_score"] == 92.0


def test_processing_time_is_measured(
    mock_jd_analysis,
    mock_candidate_a,
):
    """Processing time should be a reasonable positive value."""
    mock_jd = MagicMock()
    mock_jd.analyze.return_value = mock_jd_analysis

    mock_ranker = MagicMock()
    mock_ranker.rank_candidates.return_value = [(1, 92.0)]

    mock_conn = MagicMock()

    with patch("agents.orchestrator.get_db_connection", return_value=mock_conn):
        with patch(
            "agents.orchestrator.get_candidates_by_ids",
            return_value=[mock_candidate_a],
        ):
            with patch("agents.orchestrator.add_job_description", return_value=42):
                with patch("agents.orchestrator.add_shortlist_batch", return_value=1):
                    orchestrator = RecruitmentOrchestrator(
                        jd_analyst=mock_jd,
                        candidate_ranker=mock_ranker,
                    )
                    result = orchestrator.run_recruitment_pipeline(
                        SAMPLE_JD_TEXT, top_k=10
                    )

    # Processing time should be non-negative (zero is possible with mocked agents)
    assert result["processing_time_ms"] >= 0
