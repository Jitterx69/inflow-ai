import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from ml.models.broca.orchestrator import Orchestrator

def verify_cortex():
    print("--- Starting Cortex Verification ---")
    orchestrator = Orchestrator()
    
    # Test Case 1: Safe and Aligned Idea
    print("\n[Test Case 1] Safe and Aligned Idea")
    idea_safe = {
        "topic": "Python Programming",
        "topics": ["tech", "coding", "python"],
        "format": "Tutorial"
    }
    creator_tech = {
        "primary_topics": ["tech", "ai", "coding"],
        "tone_vector": "Professional",
        "risk_tolerance": 0.5
    }
    
    result_safe = orchestrator.create_content(idea_safe, creator_tech)
    
    if result_safe:
        print("Result: Success")
        print(f"Risk Safe: {result_safe.risk_assessment.is_safe}")
        print(f"Viability Score (from trace): {find_trace_output(result_safe, 'Cortex Viability', 'viability_score')}")
    else:
        print("Result: Failed (Unexpected)")

    # Test Case 2: Unsafe Content
    print("\n[Test Case 2] Unsafe Content (Risk Trigger)")
    # Force the "script" generation to include a risky keyword. 
    # Since we are mocking Broca, we can't easily force the *output* of generation 
    # unless we mock the generator or send an idea that triggers a hardcoded risky response.
    # However, the current Mock Generator is simple. 
    # Let's test the Risk Engine DIRECTLY for this case to be sure, 
    # or rely on the Orchestrator pass-through if we modify the input to be "risky" 
    # (but the input to orchestrator is metadata, and script is generated).
    
    # HACK: For verification, we will manually check RiskEngine with a known risky string
    from ml.models.cortex.risk import RiskEngine
    risk_engine = RiskEngine()
    risky_script = "This is a scam to get free money!"
    print(f"Testing Risk Engine directly with: '{risky_script}'")
    assessment = risk_engine.assess_risk(risky_script, creator_tech)
    print(f"Is Safe: {assessment.is_safe}")
    print(f"Reasons: {assessment.reasons}")
    
    # Test Case 3: Low Viability (Misalignment)
    print("\n[Test Case 3] Low Viability (Misalignment)")
    creator_cooking = {
        "primary_topics": ["cooking", "food"],
        "risk_tolerance": 0.5
    }
    # Using the same tech idea
    # Orchestrator doesn't block on low viability yet, but we check the score
    result_misaligned = orchestrator.create_content(idea_safe, creator_cooking)
    score = find_trace_output(result_misaligned, 'Cortex Viability', 'viability_score')
    print(f"Viability Score: {score}")
    
    print("\n--- Verification Complete ---")

def find_trace_output(result, step_name, key):
    if not result or not result.audit_event:
        return "N/A"
    
    for trace in result.audit_event.traces:
        if trace.step == step_name:
            return trace.outputs.get(key, "Key Not Found")
            
    return "Step Not Found"

if __name__ == "__main__":
    verify_cortex()
