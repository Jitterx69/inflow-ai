from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from ml.models.cortex.risk import RiskEngine, RiskAssessment
from ml.models.cortex.viability import ViabilityScorer
from ml.models.governance import AuditLogger, ReasoningTrace, AuditEvent

class ContentResult(BaseModel):
    script: str
    caption: str
    hashtags: List[str]
    risk_assessment: RiskAssessment
    audit_event: Optional[AuditEvent] = None

    class Config:
        arbitrary_types_allowed = True

class Orchestrator:
    """
    Coordinates content generation and validation.
    """
    
    def __init__(self):
        self.risk_engine = RiskEngine()
        self.viability_scorer = ViabilityScorer()
        self.audit_logger = AuditLogger()
    
    def create_content(self, idea: Dict[str, Any], creator_profile: Dict[str, Any]) -> ContentResult:
        traces = []
        
        # 1. Setup Phase
        setup_trace = ReasoningTrace("Setup")
        topic = idea.get("topic", "General")
        tone = creator_profile.get("tone_vector") or creator_profile.get("tone") or "Neutral"
        
        setup_trace.log_input("topic", topic)
        setup_trace.log_input("tone", tone)
        
        # Derive constraints
        constraints = []
        if tone == "Professional":
            msg = "Use formal language"
            constraints.append(msg)
            setup_trace.add_reason(f"Applied 'formal language' constraint based on Professional tone")
        
        traces.append(setup_trace)
        
        # 2. Viability Phase
        viability_trace = ReasoningTrace("Cortex Viability")
        score = self.viability_scorer.score_idea(idea, creator_profile)
        viability_trace.log_output("viability_score", score)
        traces.append(viability_trace)
        
        # 3. Generation Phase (Broca)
        broca_trace = ReasoningTrace("Broca")
        
        script_content = f"Script for {topic} in {tone} tone."
        if constraints:
            script_content += f" Constraints applied: {', '.join(constraints)}"
        
        caption = f"Check out my thoughts on {topic}! #{tone}"
        
        broca_trace.log_output("generated_script_length", len(script_content))
        traces.append(broca_trace)
        
        # 4. Risk Phase
        risk_trace = ReasoningTrace("Cortex Risk")
        # Check risk on the generated content
        risk_assessment = self.risk_engine.assess_risk(script_content, creator_profile)
        
        risk_trace.log_output("risk_safe", risk_assessment.is_safe)
        risk_trace.log_output("risk_score", risk_assessment.score)
        traces.append(risk_trace)
        
        # Handle Output
        final_script = script_content
        final_caption = caption
        event_type = "content_generation_success"
        
        if not risk_assessment.is_safe:
            final_script = ""
            final_caption = ""
            event_type = "content_generation_blocked"
            
        hashtags = [f"#{topic.replace(' ', '')}", "#FYP", "#Trending"]
        
        # Create Audit Event
        audit_event = self.audit_logger.log_event(event_type, traces)
        
        return ContentResult(
            script=final_script,
            caption=final_caption,
            hashtags=hashtags,
            risk_assessment=risk_assessment,
            audit_event=audit_event
        )
