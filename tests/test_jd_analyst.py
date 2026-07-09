import json
from unittest.mock import MagicMock

import pytest

from agents.jd_analyst import JDAnalysis, JDAnalystAgent

# Sample job description text used across tests
SAMPLE_JD = """
We are looking for a Senior Python Developer with 5+ years of experience.
Required skills: Python, Django, PostgreSQL, REST APIs.
Preferred skills: AWS, Docker, Kubernetes.
Education: Bachelor's in Computer Science or related field.
The role involves leading a team of 4 developers to build scalable web applications.
"""

# Valid JSON response that the mock LLM returns
MOCK_JSON = json.dumps({
    "required_skills": ["Python", "Django", "PostgreSQL", "REST APIs"],
    "preferred_skills": ["AWS", "Docker", "Kubernetes"],
    "min_experience_years": 5.0,
    "education_required": "Bachelor's in Computer Science or related field",
    "seniority_level": "Senior",
    "role_summary": "Senior Python Developer to lead a team of 4 developers building scalable web applications.",
    "search_query": "Senior Python Developer Django PostgreSQL REST APIs AWS Docker Kubernetes"
})


def test_jd_analysis_model_creation():
    """Test that JDAnalysis model can be created with all required fields."""
    analysis = JDAnalysis(
        required_skills=["Python", "SQL"],
        preferred_skills=["AWS", "Docker"],
        min_experience_years=3.0,
        education_required="Bachelor's in Computer Science",
        seniority_level="Mid",
        role_summary="A software engineer role",
        search_query="Python developer",
    )

    assert analysis.required_skills == ["Python", "SQL"]
    assert analysis.preferred_skills == ["AWS", "Docker"]
    assert analysis.min_experience_years == 3.0
    assert analysis.education_required == "Bachelor's in Computer Science"
    assert analysis.seniority_level == "Mid"
    assert analysis.role_summary == "A software engineer role"
    assert analysis.search_query == "Python developer"


def test_analyze_job_description():
    """Test successful analysis returns a valid JDAnalysis object."""
    agent = JDAnalystAgent()
    agent.chain = MagicMock()
    agent.chain.invoke.return_value = MOCK_JSON

    result = agent.analyze(SAMPLE_JD)

    assert isinstance(result, JDAnalysis)
    assert "Python" in result.required_skills
    assert "Django" in result.required_skills
    assert "AWS" in result.preferred_skills
    assert result.min_experience_years == 5.0
    assert result.seniority_level == "Senior"
    assert "Bachelor" in result.education_required
    assert "Senior Python Developer" in result.search_query


def test_analyze_output_structure():
    """Test that the output contains all 7 required fields from the Master Guide."""
    agent = JDAnalystAgent()
    agent.chain = MagicMock()
    agent.chain.invoke.return_value = MOCK_JSON

    result = agent.analyze(SAMPLE_JD)

    # Verify all fields from the spec are present and non-empty
    assert isinstance(result.required_skills, list)
    assert len(result.required_skills) > 0

    assert isinstance(result.preferred_skills, list)
    assert len(result.preferred_skills) > 0

    assert isinstance(result.min_experience_years, float)
    assert result.min_experience_years >= 0

    assert isinstance(result.education_required, str)
    assert len(result.education_required) > 0

    assert isinstance(result.seniority_level, str)
    assert result.seniority_level in ("Junior", "Mid", "Senior", "Lead")

    assert isinstance(result.role_summary, str)
    assert len(result.role_summary) > 0

    assert isinstance(result.search_query, str)
    assert len(result.search_query) > 0


def test_analyze_empty_jd_raises_error():
    """Test that empty job description raises ValueError."""
    agent = JDAnalystAgent()

    with pytest.raises(ValueError, match="non-empty"):
        agent.analyze("")

    with pytest.raises(ValueError, match="non-empty"):
        agent.analyze("   ")

    with pytest.raises(ValueError, match="non-empty"):
        agent.analyze(None)  # type: ignore


def test_analyze_retry_then_succeed():
    """Test retry logic: first 2 attempts fail, 3rd succeeds."""
    agent = JDAnalystAgent(max_retries=3)
    agent.chain = MagicMock()

    side_effects = [
        json.JSONDecodeError("Invalid JSON", "", 0),
        json.JSONDecodeError("Invalid JSON", "", 0),
        MOCK_JSON,
    ]
    agent.chain.invoke.side_effect = side_effects

    result = agent.analyze(SAMPLE_JD)

    assert isinstance(result, JDAnalysis)
    assert "Python" in result.required_skills


def test_analyze_all_retries_fail():
    """Test that RuntimeError is raised when all retry attempts fail."""
    agent = JDAnalystAgent(max_retries=3)
    agent.chain = MagicMock()
    agent.chain.invoke.side_effect = Exception("API error")

    with pytest.raises(RuntimeError, match="3 attempts"):
        agent.analyze(SAMPLE_JD)


def test_analyze_single_retry_then_succeed():
    """Test with max_retries=1: the single attempt fails, no retries left."""
    agent = JDAnalystAgent(max_retries=1)
    agent.chain = MagicMock()
    agent.chain.invoke.side_effect = Exception("API error")

    with pytest.raises(RuntimeError, match="1 attempts"):
        agent.analyze(SAMPLE_JD)


def test_analyze_handles_markdown_code_blocks():
    """Test that response wrapped in markdown code blocks is parsed correctly."""
    agent = JDAnalystAgent()
    agent.chain = MagicMock()

    markdown_response = f"```json\n{MOCK_JSON}\n```"
    agent.chain.invoke.return_value = markdown_response

    result = agent.analyze(SAMPLE_JD)

    assert isinstance(result, JDAnalysis)
    assert result.min_experience_years == 5.0


def test_analyze_handles_code_blocks_without_language():
    """Test that response in plain code blocks (no json tag) is parsed."""
    agent = JDAnalystAgent()
    agent.chain = MagicMock()

    markdown_response = f"```\n{MOCK_JSON}\n```"
    agent.chain.invoke.return_value = markdown_response

    result = agent.analyze(SAMPLE_JD)

    assert isinstance(result, JDAnalysis)
    assert result.seniority_level == "Senior"


def test_jd_analysis_default_temperature():
    """Test that default temperature is 0.1 as specified in Master Guide."""
    agent = JDAnalystAgent()
    assert agent.temperature == 0.1


def test_jd_analysis_default_max_retries():
    """Test that default max_retries is 3 as specified in Master Guide."""
    agent = JDAnalystAgent()
    assert agent.max_retries == 3
