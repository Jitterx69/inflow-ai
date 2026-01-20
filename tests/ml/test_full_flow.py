import pytest
from ml.models.broca.orchestrator import Orchestrator

def test_full_intelligence_flow():
    orchestrator = Orchestrator()
    
    idea = {"topic": "AI Ethics", "format": "Docu-style"}
    creator = {
        "primary_topics": ["AI", "Society"],
        "tone_vector": "Professional",
        "risk_tolerance": 0.8 # High tolerance for sensitive topics
    }
    
    # Run the brain
    result = orchestrator.create_content(idea, creator)
    
    # 1. Check Content Output
    assert result.script != ""
    assert "AI Ethics" in result.script
    assert "Constraints applied: Use formal language" in result.script # From generator mock
    
    # 2. Check Governance / Audit
    assert result.audit_event is not None
    assert result.audit_event.event_type == "content_generation_success"
    
    # 3. Check Explainability Traces
    traces = result.audit_event.traces
    assert len(traces) == 4 # Setup, Viability, Broca, Risk
    
    setup_trace = traces[0]
    assert setup_trace.step == "Setup"
    assert "applied 'formal language'" in setup_trace.reasoning[0].lower()
    
    risk_trace = traces[3]
    assert risk_trace.step == "Cortex Risk"
    assert risk_trace.outputs["risk_safe"] == "True"

def test_blocked_content_flow():
    orchestrator = Orchestrator()
    
    # Risky content idea
    idea = {"topic": "how to gamble", "format": "Short"}
    creator = {
        "primary_topics": ["Gaming"],
        "tone_vector": "Casual",
        "risk_tolerance": 0.1 # Zero tolerance
    }
    
    result = orchestrator.create_content(idea, creator)
    
    # 1. Check Content Blocked
    assert result.script == ""
    
    # 2. Check Governance Log for blockage
    assert result.audit_event is not None
    assert result.audit_event.event_type == "content_generation_blocked"
    
    # 3. Check Trace for Reason
    risk_trace = result.audit_event.traces[-1]
    assert risk_trace.outputs["risk_safe"] == "False"
