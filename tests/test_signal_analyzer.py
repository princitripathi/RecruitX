import pytest
from agents.signal_analyzer import SignalAnalyzerAgent


def test_recency_scores():
    agent = SignalAnalyzerAgent()
    
    # Threshold <= 7 -> 100
    assert agent.calculate_recency_score(0) == 100.0
    assert agent.calculate_recency_score(7) == 100.0
    
    # Threshold <= 30 -> 80
    assert agent.calculate_recency_score(8) == 80.0
    assert agent.calculate_recency_score(30) == 80.0
    
    # Threshold <= 90 -> 60
    assert agent.calculate_recency_score(31) == 60.0
    assert agent.calculate_recency_score(90) == 60.0
    
    # Threshold <= 180 -> 40
    assert agent.calculate_recency_score(91) == 40.0
    assert agent.calculate_recency_score(180) == 40.0
    
    # Threshold <= 365 -> 20
    assert agent.calculate_recency_score(181) == 20.0
    assert agent.calculate_recency_score(365) == 20.0
    
    # Threshold > 365 -> 5
    assert agent.calculate_recency_score(366) == 5.0
    assert agent.calculate_recency_score(999) == 5.0
    
    # None -> defaults to high days (5.0)
    assert agent.calculate_recency_score(None) == 5.0


def test_experience_match_scores():
    agent = SignalAnalyzerAgent()
    
    # Case: required_experience <= 0 -> should return 100
    assert agent.calculate_experience_match(5.0, 0.0) == 100.0
    assert agent.calculate_experience_match(5.0, -2.0) == 100.0
    assert agent.calculate_experience_match(5.0, None) == 100.0
    
    # Case: candidate_experience is null/invalid -> should return 30 (since required is > 0 and ratio < 0.6)
    assert agent.calculate_experience_match(None, 5.0) == 30.0
    assert agent.calculate_experience_match(-1.0, 5.0) == 30.0

    # Ratio >= 1.0 (candidate 5 years, required 5 years -> 1.0 ratio -> 100)
    assert agent.calculate_experience_match(5.0, 5.0) == 100.0
    assert agent.calculate_experience_match(6.0, 5.0) == 100.0
    
    # Ratio >= 0.8 (candidate 4 years, required 5 years -> 0.8 ratio -> 80)
    assert agent.calculate_experience_match(4.0, 5.0) == 80.0
    assert agent.calculate_experience_match(4.5, 5.0) == 80.0
    
    # Ratio >= 0.6 (candidate 3 years, required 5 years -> 0.6 ratio -> 60)
    assert agent.calculate_experience_match(3.0, 5.0) == 60.0
    assert agent.calculate_experience_match(3.5, 5.0) == 60.0
    
    # Ratio < 0.6 (candidate 2 years, required 5 years -> 0.4 ratio -> 30)
    assert agent.calculate_experience_match(2.0, 5.0) == 30.0
    assert agent.calculate_experience_match(0.0, 5.0) == 30.0


def test_analyze_signals_full_calculation():
    agent = SignalAnalyzerAgent()
    
    # Candidate profile:
    # - Completeness: 85 (score = 85.0)
    # - Recency: 12 days (score = 80.0)
    # - Experience: 5.0 years
    # Required experience: 5.0 years (ratio = 1.0 -> score = 100.0)
    # Expected weighted score:
    # (85.0 * 0.40) + (80.0 * 0.40) + (100.0 * 0.20)
    # = 34.0 + 32.0 + 20.0 = 86.0
    candidate = {
        "id": 1,
        "profile_completeness": 85,
        "last_active_days": 12,
        "experience_years": 5.0
    }
    
    result = agent.analyze_signals(candidate, required_experience=5.0)
    
    assert result["completeness_score"] == 85.0
    assert result["recency_score"] == 80.0
    assert result["experience_match"] == 100.0
    assert result["signal_score"] == 86.0


def test_analyze_signals_missing_keys():
    agent = SignalAnalyzerAgent()
    
    # Empty candidate dictionary
    # Completeness defaults to 0 (score = 0.0)
    # Recency defaults to 999 (score = 5.0)
    # Experience defaults to 0 (score = 30.0 if required experience is 5.0)
    # Expected weighted score:
    # (0.0 * 0.40) + (5.0 * 0.40) + (30.0 * 0.20) = 0.0 + 2.0 + 6.0 = 8.0
    candidate = {}
    
    result = agent.analyze_signals(candidate, required_experience=5.0)
    
    assert result["completeness_score"] == 0.0
    assert result["recency_score"] == 5.0
    assert result["experience_match"] == 30.0
    assert result["signal_score"] == 8.0


def test_analyze_signals_invalid_types():
    agent = SignalAnalyzerAgent()
    
    # Profile completeness and experience are strings that can be converted, or invalid
    candidate = {
        "profile_completeness": "90",
        "last_active_days": "invalid_integer_should_fallback",
        "experience_years": "4.0"
    }
    
    # Since last_active_days is invalid, get() works but exception is avoided or handled
    # If ValueError occurs inside try block, exception handler yields 0 scores
    result = agent.analyze_signals(candidate, required_experience=5.0)
    
    # Since "invalid_integer_should_fallback" will fail conversion inside calculate_recency_score,
    # it raises an exception which is caught in analyze_signals, returning the fallback dictionary.
    assert result["signal_score"] == 0.0
    assert result["recency_score"] == 0.0
    assert result["completeness_score"] == 0.0
    assert result["experience_match"] == 0.0
