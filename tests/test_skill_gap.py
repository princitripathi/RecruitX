import pytest
from scoring.skill_gap import SkillGapAnalyzer


def test_perfect_match():
    """All required and preferred skills match exactly."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL", "Docker", "AWS"],
        required_skills=["Python", "SQL"],
        preferred_skills=["Docker", "AWS"],
    )

    assert result["matched"] == ["AWS", "Docker", "Python", "SQL"]
    assert result["missing"] == []
    assert result["bonus"] == []


def test_partial_match():
    """Only some candidate skills match JD requirements."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL", "AWS"],
        required_skills=["Python", "Docker"],
        preferred_skills=["Kubernetes"],
    )

    assert result["matched"] == ["Python"]
    assert result["missing"] == ["Docker"]
    assert result["bonus"] == ["AWS", "SQL"]


def test_no_match():
    """No candidate skills match any JD requirement."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Cooking", "Driving"],
        required_skills=["Python", "Docker"],
        preferred_skills=["Kubernetes"],
    )

    assert result["matched"] == []
    assert result["missing"] == ["Docker", "Python"]
    assert result["bonus"] == ["Cooking", "Driving"]


def test_bonus_skills_only():
    """All candidate skills are bonus (JD has no required/preferred)."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL", "AWS"],
        required_skills=None,
        preferred_skills=None,
    )

    assert result["matched"] == []
    assert result["missing"] == []
    assert result["bonus"] == ["AWS", "Python", "SQL"]


def test_empty_candidate_skills():
    """Empty candidate skills list."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=[],
        required_skills=["Python", "Docker"],
        preferred_skills=["AWS"],
    )

    assert result["matched"] == []
    assert result["missing"] == ["Docker", "Python"]
    assert result["bonus"] == []


def test_empty_jd_skills():
    """No required or preferred skills specified."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL"],
        required_skills=[],
        preferred_skills=[],
    )

    assert result["matched"] == []
    assert result["missing"] == []
    assert result["bonus"] == ["Python", "SQL"]


def test_all_empty():
    """All inputs are empty."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=[],
        required_skills=[],
        preferred_skills=[],
    )

    assert result["matched"] == []
    assert result["missing"] == []
    assert result["bonus"] == []


def test_case_insensitive_matching():
    """Matching should ignore case differences. Output uses candidate's casing."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["python", "sql", "aws"],
        required_skills=["Python", "SQL"],
        preferred_skills=["AWS"],
    )

    # Candidate's casing is preserved: "aws" not "AWS"
    assert result["matched"] == ["aws", "python", "sql"]
    assert result["missing"] == []
    assert result["bonus"] == []


def test_mixed_case_matching():
    """Skills with mixed casing should match regardless."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["PyThOn", "DjanGO"],
        required_skills=["python", "django"],
        preferred_skills=[],
    )

    assert result["matched"] == ["DjanGO", "PyThOn"]
    assert result["missing"] == []
    assert result["bonus"] == []


def test_whitespace_handling():
    """Leading and trailing whitespace should be stripped before matching."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["  Python  ", " SQL "],
        required_skills=["Python", "  SQL  "],
        preferred_skills=[],
    )

    assert result["matched"] == ["Python", "SQL"]
    assert result["missing"] == []
    assert result["bonus"] == []


def test_duplicate_skills_in_candidate():
    """Duplicate skills in candidate list should appear only once."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "Python", "SQL", "python"],
        required_skills=["Python", "Docker"],
        preferred_skills=[],
    )

    # "Python" appears only once in matched (first occurrence casing preserved)
    assert result["matched"] == ["Python"]
    assert result["missing"] == ["Docker"]
    assert result["bonus"] == ["SQL"]


def test_duplicate_skills_in_required():
    """Duplicate skills in required list should not cause duplicates in missing."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python"],
        required_skills=["Docker", "Docker", "docker"],
        preferred_skills=[],
    )

    # "Docker" appears only once in missing (deduplicated, first occurrence casing)
    # "Python" is not required or preferred, so it is bonus
    assert result["matched"] == []
    assert result["missing"] == ["Docker"]
    assert result["bonus"] == ["Python"]


def test_duplicate_skills_across_required_and_preferred():
    """A skill in both required and preferred should not duplicate in matched."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python"],
        required_skills=["Python"],
        preferred_skills=["Python"],
    )

    # "Python" should appear only once in matched
    assert result["matched"] == ["Python"]
    assert result["missing"] == []
    assert result["bonus"] == []


def test_output_order_alphabetical():
    """Output lists must be sorted alphabetically."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Zebra", "Alpha", "Beta"],
        required_skills=["Alpha", "Zebra"],
        preferred_skills=["Gamma"],
    )

    assert result["matched"] == ["Alpha", "Zebra"]
    assert result["bonus"] == ["Beta"]
    assert result["matched"] == sorted(result["matched"])
    assert result["missing"] == sorted(result["missing"])
    assert result["bonus"] == sorted(result["bonus"])


def test_only_required_skills():
    """Only required skills provided, no preferred."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL", "Docker"],
        required_skills=["Python", "Docker", "Kubernetes"],
        preferred_skills=None,
    )

    assert result["matched"] == ["Docker", "Python"]
    assert result["missing"] == ["Kubernetes"]
    assert result["bonus"] == ["SQL"]


def test_only_preferred_skills():
    """Only preferred skills provided, no required."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "SQL", "Docker"],
        required_skills=None,
        preferred_skills=["Python", "Docker"],
    )

    assert result["matched"] == ["Docker", "Python"]
    assert result["missing"] == []
    assert result["bonus"] == ["SQL"]


def test_invalid_candidate_skills_none():
    """None as candidate_skills should raise ValueError."""
    analyzer = SkillGapAnalyzer()
    with pytest.raises(ValueError, match="candidate_skills must be a list"):
        analyzer.analyze(candidate_skills=None)  # type: ignore


def test_invalid_candidate_skills_string():
    """String as candidate_skills should raise ValueError."""
    analyzer = SkillGapAnalyzer()
    with pytest.raises(ValueError, match="candidate_skills must be a list"):
        analyzer.analyze(candidate_skills="Python, SQL")  # type: ignore


def test_original_casing_preserved():
    """Output should preserve the original casing from input."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["PYTHON", "sql"],
        required_skills=["python"],
        preferred_skills=[],
    )

    # matched should use candidate's casing "PYTHON" (first occurrence)
    assert result["matched"] == ["PYTHON"]
    assert result["bonus"] == ["sql"]


def test_original_casing_missing_uses_required():
    """Missing skills should use the casing from required_skills."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["python"],
        required_skills=["DOCKER", "kubernetes"],
        preferred_skills=[],
    )

    # missing uses required_map casing (first occurrence)
    assert result["missing"] == ["DOCKER", "kubernetes"]


def test_empty_string_skill_ignored():
    """Empty string skills should be silently ignored."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "", "  "],
        required_skills=["Python", "Docker"],
        preferred_skills=[],
    )

    assert result["matched"] == ["Python"]
    assert result["missing"] == ["Docker"]
    assert result["bonus"] == []


def test_whitespace_only_skills_ignored():
    """Whitespace-only skills should be silently ignored."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "   ", "\t"],
        required_skills=["Python"],
        preferred_skills=[],
    )

    assert result["matched"] == ["Python"]
    assert result["missing"] == []
    assert result["bonus"] == []


def test_duplicate_casing_and_whitespace_in_candidate():
    """Multiple variations of the same skill resolve to one match."""
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze(
        candidate_skills=["Python", "python", " PYTHON "],
        required_skills=["Python"],
        preferred_skills=[],
    )

    # All three normalize to "python"; first occurrence "Python" is preserved
    assert result["matched"] == ["Python"]
    assert result["missing"] == []
    assert result["bonus"] == []
