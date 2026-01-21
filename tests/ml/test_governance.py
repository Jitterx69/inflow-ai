import pytest
import json
from ml.models.governance import ReasoningTrace, AuditLogger, AuditEvent

def test_reasoning_trace():
    trace = ReasoningTrace("RiskCheck")
    trace.log_input("content", "hello world")
    trace.log_output("is_safe", True)
    trace.add_reason("No risky keywords found")
    
    data = trace.to_dict()
    assert data["step"] == "RiskCheck"
    assert data["inputs"]["content"] == "hello world"
    assert "No risky keywords found" in data["reasoning"]

def test_audit_logging():
    logger = AuditLogger()
    
    trace1 = ReasoningTrace("Step1")
    trace1.add_reason("Init")
    
    trace2 = ReasoningTrace("Step2")
    trace2.add_reason("Done")
    
    event = logger.log_event("ContentGeneration", [trace1, trace2])
    
    assert event.event_type == "ContentGeneration"
    assert len(event.traces) == 2
    assert len(logger.events) == 1
    
    # Check JSON serialization
    json_str = event.to_json()
    data = json.loads(json_str)
    assert data["event_type"] == "ContentGeneration"
    assert len(data["traces"]) == 2
