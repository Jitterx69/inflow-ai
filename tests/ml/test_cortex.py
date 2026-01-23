import pytest
from ml.models.cortex.viability import ViabilityScorer
from ml.models.cortex.risk import RiskEngine

@pytest.fixture
def viability_scorer():
    return ViabilityScorer()

@pytest.fixture
def risk_engine():
    return RiskEngine()

def test_viability_score_alignment(viability_scorer):
    idea = {"topics": ["tech", "ai"]}
    creator = {"primary_topics": ["tech", "coding"]}
    
    score = viability_scorer.score_idea(idea, creator)
    # Base 0.5 + 0.3 alignment = 0.8 * 100 = 80 +/- random
    assert score >= 70.0  # Allow for small negative random fluctuation
    assert score <= 100.0

def test_viability_score_misalignment(viability_scorer):
    idea = {"topics": ["cooking"]}
    creator = {"primary_topics": ["tech", "coding"]}
    
    score = viability_scorer.score_idea(idea, creator)
    # Base 0.5 - 0.1 alignment = 0.4 * 100 = 40 +/- random
    assert score <= 60.0
    assert score >= 0.0

def test_risk_safe_content(risk_engine):
    content = "This is a great tutorial on python."
    prefs = {"risk_tolerance": 0.2}
    
    assessment = risk_engine.assess_risk(content, prefs)
    assert assessment.is_safe
    assert assessment.score == 0.0
    assert "RISK_PASS" in assessment.decision_flags

def test_risk_unsafe_content(risk_engine):
    content = "Join this scam to get rich."
    prefs = {"risk_tolerance": 0.2}
    
    assessment = risk_engine.assess_risk(content, prefs)
    assert not assessment.is_safe
    assert assessment.score >= 0.9
    assert "risky keyword" in assessment.reasons[0]
    assert "RISK_KEYWORD_DETECTED" in assessment.decision_flags
    assert "RISK_FAIL" in assessment.decision_flags

def test_risk_tolerance_threshold(risk_engine):
    # 'free money' has score 0.7
    content = "Click here for free money!"
    
    # High tolerance creator should accept it
    high_tolerance_prefs = {"risk_tolerance": 0.8}
    assessment_safe = risk_engine.assess_risk(content, high_tolerance_prefs)
    assert assessment_safe.is_safe
    assert "RISK_PASS" in assessment_safe.decision_flags
    
    # Low tolerance creator should reject it
    low_tolerance_prefs = {"risk_tolerance": 0.5}
    assessment_unsafe = risk_engine.assess_risk(content, low_tolerance_prefs)
    assert not assessment_unsafe.is_safe
    assert "RISK_FAIL" in assessment_unsafe.decision_flags
