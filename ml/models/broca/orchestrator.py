from typing import Dict, Any, List
from pydantic import BaseModel
from ml.models.cortex.risk import RiskEngine, RiskAssessment

class ContentResult(BaseModel):
    script: str
    caption: str
    hashtags: List[str]
    risk_assessment: RiskAssessment

class Orchestrator:
    """
    Coordinates content generation and validation.
    """
    
    def __init__(self):
        self.risk_engine = RiskEngine()
    
    def create_content(self, idea: Dict[str, Any], creator_profile: Dict[str, Any]) -> ContentResult:
        # 1. Generate (Mock)
        topic = idea.get("topic", "General")
        tone = creator_profile.get("tone", "Neutral")
        
        script = f"Script for {topic} in {tone} tone."
        caption = f"Check out my thoughts on {topic}! #{tone}"
        
        # 2. Risk Check
        risk_assessment = self.risk_engine.assess_risk(script, creator_profile)
        
        # 3. Handle unsafe content
        if not risk_assessment.is_safe:
            # If unsafe, we might strip the script or just return flagged status
            # For this test requirement: "assert result.script == """ if fails?
            # Let's check the test expectation. 
            # "assert result.script == """
            # Okay, I will blot out the script.
            script = ""
            caption = ""
        
        # 4. Hashtags
        hashtags = [f"#{topic.replace(' ', '')}", "#FYP", "#Trending"]
        
        return ContentResult(
            script=script,
            caption=caption,
            hashtags=hashtags,
            risk_assessment=risk_assessment
        )
