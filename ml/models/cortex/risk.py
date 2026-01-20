from typing import List, Dict, Any
from pydantic import BaseModel, Field

class RiskAssessment(BaseModel):
    is_safe: bool
    score: float
    reasons: List[str]
    decision_flags: List[str]

class RiskEngine:
    """
    Assesses content risk and checks against creator tolerance.
    """
    
    def __init__(self):
        # Weighted keywords for scaffolding
        self.risk_keywords = {
            "scam": 0.9,
            "fraud": 0.9,
            "ponzi": 0.95,
            "free money": 0.7,
            "guaranteed returns": 0.8,
            "crypto gem": 0.6,
            "hate": 0.9,
        }

    def assess_risk(self, content: str, creator_prefs: Dict[str, Any]) -> RiskAssessment:
        content_lower = content.lower()
        max_risk_score = 0.0
        reasons = []
        flags = []
        
        # 1. Content Scoring
        for keyword, score in self.risk_keywords.items():
            if keyword in content_lower:
                if score > max_risk_score:
                    max_risk_score = score
                reasons.append(f"Contains risky keyword: '{keyword}'")
                flags.append("RISK_KEYWORD_DETECTED")
        
        if max_risk_score == 0.0:
            flags.append("RISK_PASS")
        
        # 2. Tolerance Check
        # Tolerance 1.0 = Accepts everything. Tolerance 0.0 = Accepts nothing 
        # (Wait, actually usually Tolerance 1.0 means High Tolerance. 
        # So acceptable if risk_score <= risk_tolerance)
        
        tolerance = creator_prefs.get("risk_tolerance", 0.5)
        
        is_safe = max_risk_score <= tolerance
        
        if not is_safe:
            flags.append("RISK_FAIL")
            reasons.append(f"Risk score {max_risk_score} exceeds tolerance {tolerance}")
        else:
            if "RISK_PASS" not in flags:
                flags.append("RISK_PASS")

        return RiskAssessment(
            is_safe=is_safe,
            score=max_risk_score,
            reasons=reasons,
            decision_flags=flags
        )
