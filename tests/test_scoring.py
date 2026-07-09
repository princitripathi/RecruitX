import pytest
from scoring.scoring_engine import ScoringEngine


def test_skill_score_perfect_match():
    engine = ScoringEngine()
    candidate_skills = ["Python", "SQL", "FastAPI", "Docker"]
    required_skills = ["Python", "SQL", "FastAPI", "Docker"]
    preferred_skills = ["AWS", "Kubernetes"]

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Required: 4/4 = 100%, Preferred: 0/2 = 0%
    # Skill Score = (100.0 x 0.70) + (0.0 x 0.30) = 70.0
    assert score == 70.0


def test_skill_score_no_match():
    engine = ScoringEngine()
    candidate_skills = ["Cooking", "Driving"]
    required_skills = ["Python", "SQL", "Docker"]
    preferred_skills = ["AWS", "Kubernetes"]

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Required: 0/3 = 0%, Preferred: 0/2 = 0%
    # Skill Score = (0.0 x 0.70) + (0.0 x 0.30) = 0.0
    assert score == 0.0


def test_skill_score_partial_match():
    engine = ScoringEngine()
    candidate_skills = ["Python", "SQL", "AWS"]
    required_skills = ["Python", "SQL", "Docker", "FastAPI"]
    preferred_skills = ["AWS", "Kubernetes"]

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Required: 2/4 = 50%, Preferred: 1/2 = 50%
    # Skill Score = (50.0 x 0.70) + (50.0 x 0.30) = 35.0 + 15.0 = 50.0
    assert score == 50.0


def test_skill_score_no_required_skills():
    engine = ScoringEngine()
    candidate_skills = ["Python", "SQL"]
    required_skills = []
    preferred_skills = ["AWS", "Kubernetes"]

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Required: empty -> 100%, Preferred: 0/2 = 0%
    # Skill Score = (100.0 x 0.70) + (0.0 x 0.30) = 70.0
    assert score == 70.0


def test_skill_score_no_preferred_skills():
    engine = ScoringEngine()
    candidate_skills = ["Python", "SQL"]
    required_skills = ["Python", "SQL"]
    preferred_skills = []

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Required: 2/2 = 100%, Preferred: empty -> 100%
    # Skill Score = (100.0 x 0.70) + (100.0 x 0.30) = 70.0 + 30.0 = 100.0
    assert score == 100.0


def test_skill_score_none_skills():
    engine = ScoringEngine()
    candidate_skills = ["Python"]
    required_skills = None
    preferred_skills = None

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Both empty -> both 100%
    # Skill Score = (100.0 x 0.70) + (100.0 x 0.30) = 100.0
    assert score == 100.0


def test_skill_score_case_insensitive():
    engine = ScoringEngine()
    candidate_skills = ["python", "sql"]
    required_skills = ["Python", "SQL"]
    preferred_skills = []

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills)

    # Required: 2/2 = 100% (case-insensitive match), Preferred: empty -> 100%
    # Skill Score = (100.0 x 0.70) + (100.0 x 0.30) = 100.0
    assert score == 100.0


def test_skill_score_whitespace_handling():
    engine = ScoringEngine()
    candidate_skills = ["  Python  ", "SQL "]
    required_skills = ["Python", "SQL"]

    score = engine.calculate_skill_score(candidate_skills, required_skills, preferred_skills=[])

    assert score == 100.0


def test_final_score_standard_case():
    engine = ScoringEngine()
    semantic = 90.0
    skill = 80.0
    signal = 70.0

    final = engine.calculate_final_score(semantic, skill, signal)

    # (90.0 x 0.50) + (80.0 x 0.30) + (70.0 x 0.20) = 45.0 + 24.0 + 14.0 = 83.0
    assert final == 83.0


def test_final_score_perfect():
    engine = ScoringEngine()
    final = engine.calculate_final_score(100.0, 100.0, 100.0)

    # (100.0 x 0.50) + (100.0 x 0.30) + (100.0 x 0.20) = 50.0 + 30.0 + 20.0 = 100.0
    assert final == 100.0


def test_final_score_zero():
    engine = ScoringEngine()
    final = engine.calculate_final_score(0.0, 0.0, 0.0)

    assert final == 0.0


def test_final_score_score_range():
    engine = ScoringEngine()
    # Test that scores are properly bounded (the engine doesn't clamp, but verifies correctness)
    final = engine.calculate_final_score(50.0, 50.0, 50.0)

    # (50.0 x 0.50) + (50.0 x 0.30) + (50.0 x 0.20) = 25.0 + 15.0 + 10.0 = 50.0
    assert final == 50.0


def test_ranking_order():
    engine = ScoringEngine()
    candidates = [
        {"id": 1, "semantic": 90.0, "skill": 80.0, "signal": 70.0},
        {"id": 2, "semantic": 60.0, "skill": 90.0, "signal": 80.0},
        {"id": 3, "semantic": 70.0, "skill": 60.0, "signal": 90.0},
    ]

    scored = []
    for c in candidates:
        final = engine.calculate_final_score(c["semantic"], c["skill"], c["signal"])
        scored.append((c["id"], final))

    # Sort by final score descending
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)

    # Verify ranking order (highest score first)
    for i in range(len(ranked) - 1):
        assert ranked[i][1] >= ranked[i + 1][1]

    # Verify specific values:
    # Candidate 1: (90.0 x 0.50) + (80.0 x 0.30) + (70.0 x 0.20) = 45.0 + 24.0 + 14.0 = 83.0
    # Candidate 2: (60.0 x 0.50) + (90.0 x 0.30) + (80.0 x 0.20) = 30.0 + 27.0 + 16.0 = 73.0
    # Candidate 3: (70.0 x 0.50) + (60.0 x 0.30) + (90.0 x 0.20) = 35.0 + 18.0 + 18.0 = 71.0
    assert ranked[0][0] == 1
    assert ranked[0][1] == 83.0
    assert ranked[1][0] == 2
    assert ranked[1][1] == 73.0
    assert ranked[2][0] == 3
    assert ranked[2][1] == 71.0


def test_skill_score_empty_candidate_skills():
    engine = ScoringEngine()
    score = engine.calculate_skill_score([], ["Python", "SQL"], ["AWS"])

    # Required: 0/2 = 0%, Preferred: 0/1 = 0%
    # Skill Score = (0.0 x 0.70) + (0.0 x 0.30) = 0.0
    assert score == 0.0
