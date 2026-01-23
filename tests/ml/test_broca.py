import pytest
from ml.models.broca.orchestrator import Orchestrator

@pytest.fixture
def orchestrator():
    return Orchestrator()

def test_happy_path_orchestration(orchestrator):
    idea = {"topic": "AI Agents", "format": "Short"}
    creator = {
        "primary_topics": ["AI"], 
        "tone": "Excited",
        "risk_tolerance": 0.5
    }
    
    result = orchestrator.create_content(idea, creator)
    
    assert result is not None
    assert "AI Agents" in result.script
    assert result.risk_assessment.is_safe
    assert len(result.hashtags) > 0
    assert "Excited" in result.caption or "#Excited" in result.caption

def test_risk_blocking_orchestration(orchestrator):
    # Idea that leads to risky content (mocked via generation injection or keyword if I could control generation)
    # Since generation is hardcoded safe in my mock, let's inject a "bad" constraint or rely on keywords if I can?
    # Actually, the Generator mock is static.
    # To test this, I'll need to mock the generator or subclass it, 
    # OR, rely on the fact that my risk engine checks the SCRIPT.
    # My current Generator puts the 'topic' in the script.
    
    idea = {"topic": "how to pull a scam", "format": "Short"}
    creator = {"risk_tolerance": 0.1}
    
    # "scam" is in my risk keyword list in RiskEngine
    
    result = orchestrator.create_content(idea, creator)
    
    # Needs to fail risk check
    assert result.script == ""
    assert not result.risk_assessment.is_safe
    assert "scam" in result.risk_assessment.reasons[0]
