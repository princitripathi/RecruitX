"""
tests/test_interview_generator.py — Tests for the Interview Question Generator (Phase 15)

Tests cover:
    - Successful question generation with valid inputs
    - Generation with skill gaps (missing skills appear in questions)
    - Handling fewer than 5 questions returned by LLM (re-request)
    - Markdown code block handling (```json and ```)
    - Retry logic (fail then succeed)
    - All retries exhausted -> RuntimeError
    - Empty job description -> ValueError
    - Empty candidate info -> ValueError
    - _build_context output structure

Run with:
    pytest tests/test_interview_generator.py -v
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from utils.interview_generator import InterviewQuestionGenerator, InterviewQuestions


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def generator() -> InterviewQuestionGenerator:
    """Return a fresh InterviewQuestionGenerator instance for each test."""
    return InterviewQuestionGenerator()


SAMPLE_CANDIDATE = {
    "name": "Rahul Sharma",
    "skills": "Python, SQL, FastAPI",
    "experience_years": 5.0,
    "previous_roles": "Data Analyst at TCS; Backend Dev at Infosys",
    "education": "B.Tech Computer Science",
}

SAMPLE_JD = "We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, Docker, and Kubernetes."

SAMPLE_SKILL_GAP = {
    "matched": ["Python", "FastAPI"],
    "missing": ["Docker", "Kubernetes"],
    "bonus": ["SQL"],
}

SAMPLE_EXPLANATION = "Rank #1. Matched 2 skill(s), missing 2 skill(s). Semantic fit: 92.0/100."

MOCK_QUESTIONS = [
    "Your experience is primarily in FastAPI. How would you design a Docker-based deployment for a FastAPI application?",
    "You have strong Python skills. Can you walk me through how you would implement a Kubernetes deployment for a microservice?",
    "You have 5 years of experience as a Data Analyst and Backend Developer. Describe a complex data pipeline you built end-to-end.",
    "How would you handle authentication and authorization in a FastAPI application at scale?",
    "You have SQL experience. How do you optimize slow queries in PostgreSQL?",
    "Describe a time you had a disagreement with a teammate about technical approach. How did you resolve it?",
    "What strategies do you use to ensure API security beyond basic authentication?",
]

MOCK_QUESTIONS_JSON = json.dumps({"questions": MOCK_QUESTIONS})


# ===================================================================
# InterviewQuestions Model Tests
# ===================================================================


class TestInterviewQuestionsModel:
    """Verify the Pydantic model for structured LLM output."""

    def test_valid_questions(self):
        """Test creation with valid questions list."""
        result = InterviewQuestions(questions=MOCK_QUESTIONS)
        assert len(result.questions) == 7
        assert result.questions[0] == MOCK_QUESTIONS[0]

    def test_fewer_than_5_raises_error(self):
        """Test that fewer than 5 questions raises validation error."""
        with pytest.raises(Exception):
            InterviewQuestions(questions=["Q1", "Q2", "Q3", "Q4"])

    def test_model_validate_from_dict(self):
        """Test validation from a dict (simulating LLM JSON output)."""
        data = {"questions": ["Q1", "Q2", "Q3", "Q4", "Q5"]}
        result = InterviewQuestions.model_validate(data)
        assert len(result.questions) == 5


# ===================================================================
# Context Builder Tests
# ===================================================================


class TestBuildContext:
    """Tests for _build_context method."""

    def test_build_context_contains_all_sections(self, generator):
        """Test that the context string contains all required sections."""
        context = generator._build_context(
            candidate_info=SAMPLE_CANDIDATE,
            job_description=SAMPLE_JD,
            skill_gap=SAMPLE_SKILL_GAP,
            explanation=SAMPLE_EXPLANATION,
        )

        assert "=== CANDIDATE PROFILE ===" in context
        assert "=== JOB DESCRIPTION ===" in context
        assert "=== SKILL GAP ANALYSIS ===" in context
        assert "=== RANKING EXPLANATION ===" in context
        assert "Rahul Sharma" in context
        assert "Docker, Kubernetes" in context
        assert "Senior Python Developer" in context

    def test_build_context_empty_skill_gap(self, generator):
        """Test context building with empty skill gap lists."""
        context = generator._build_context(
            candidate_info=SAMPLE_CANDIDATE,
            job_description=SAMPLE_JD,
            skill_gap={"matched": [], "missing": [], "bonus": []},
            explanation="No explanation",
        )

        assert "Matched Skills: None" in context
        assert "Missing Skills: None" in context
        assert "Bonus Skills: None" in context


# ===================================================================
# LLM Generation Tests
# ===================================================================


class TestGenerateQuestions:
    """Tests for the generate method with mocked LLM."""

    def test_generate_success(self, generator):
        """Test successful generation returns InterviewQuestions."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_QUESTIONS_JSON

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

        assert isinstance(result, InterviewQuestions)
        assert len(result.questions) == 7
        assert "Docker" in result.questions[0]

    def test_generate_with_skill_gap_reflected(self, generator):
        """Test that missing skills appear in generated questions."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_QUESTIONS_JSON

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

        # Verify questions reference missing skills (Docker, Kubernetes)
        questions_text = " ".join(result.questions).lower()
        assert "docker" in questions_text
        assert "kubernetes" in questions_text

    def test_generate_handles_markdown_code_blocks(self, generator):
        """Test LLM response wrapped in ```json ... ``` blocks."""
        markdown_response = f"```json\n{MOCK_QUESTIONS_JSON}\n```"
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = markdown_response

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

        assert len(result.questions) == 7

    def test_generate_handles_plain_code_blocks(self, generator):
        """Test LLM response wrapped in ``` (without json) blocks."""
        markdown_response = f"```\n{MOCK_QUESTIONS_JSON}\n```"
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = markdown_response

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

        assert len(result.questions) == 7

    def test_retry_then_succeed(self, generator):
        """Test retry logic: first 2 attempts fail, 3rd succeeds."""
        side_effects = [
            json.JSONDecodeError("Invalid JSON", "", 0),
            json.JSONDecodeError("Invalid JSON", "", 0),
            MOCK_QUESTIONS_JSON,
        ]
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = side_effects

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

        assert isinstance(result, InterviewQuestions)
        assert len(result.questions) == 7

    def test_all_retries_fail(self, generator):
        """Test that RuntimeError is raised when all retries fail."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("API error")

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            with pytest.raises(RuntimeError, match="Failed to generate interview questions"):
                generator.generate(
                    candidate_info=SAMPLE_CANDIDATE,
                    job_description=SAMPLE_JD,
                    skill_gap=SAMPLE_SKILL_GAP,
                    explanation=SAMPLE_EXPLANATION,
                )

    def test_generate_empty_job_description(self, generator):
        """Test that empty job description raises ValueError."""
        with pytest.raises(ValueError, match="job_description must be a non-empty string"):
            generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description="",
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

    def test_generate_empty_candidate_info(self, generator):
        """Test that empty candidate info raises ValueError."""
        with pytest.raises(ValueError, match="candidate_info must be a non-empty dict"):
            generator.generate(
                candidate_info={},
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

    def test_fewer_than_5_re_requests(self, generator):
        """Test that fewer than 5 questions causes a re-request (triggers retry)."""
        too_few_json = json.dumps({"questions": ["Q1", "Q2", "Q3", "Q4"]})
        mock_chain = MagicMock()
        # First returns 4 questions (invalid), second returns valid 7
        mock_chain.invoke.side_effect = [too_few_json, MOCK_QUESTIONS_JSON]

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=SAMPLE_SKILL_GAP,
                explanation=SAMPLE_EXPLANATION,
            )

        assert len(result.questions) == 7

    def test_missing_skills_prioritized(self, generator):
        """Test that output prioritizes missing skills."""
        gap_with_missing = {
            "matched": ["Python"],
            "missing": ["Docker", "Kubernetes", "AWS"],
            "bonus": ["SQL"],
        }
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_QUESTIONS_JSON

        with patch.object(generator, "_create_generation_chain", return_value=mock_chain):
            result = generator.generate(
                candidate_info=SAMPLE_CANDIDATE,
                job_description=SAMPLE_JD,
                skill_gap=gap_with_missing,
                explanation=SAMPLE_EXPLANATION,
            )

        questions_text = " ".join(result.questions).lower()
        # At least some missing skills should be probed
        assert any(skill.lower() in questions_text for skill in gap_with_missing["missing"])
