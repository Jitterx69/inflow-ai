"""
Decision Engine - Rule Pass-through Stub
Makes final decisions based on predictions.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "decision-engine", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class Config:
    SERVICE_NAME = "decision-engine"
    SERVICE_VERSION = "0.1.0"
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    rules_loaded: int
    timestamp: str


class Prediction(BaseModel):
    label: str
    confidence: float


class FeatureVector(BaseModel):
    account_id: str
    days_past_due: int = 0
    outstanding_balance: float = 0.0
    payment_history_score: float = 0.5
    contact_attempts: int = 0
    last_payment_days_ago: int = 0
    account_age_months: int = 12


class DecisionRequest(BaseModel):
    request_id: str
    account_id: str
    prediction: Prediction
    features: FeatureVector


class Decision(BaseModel):
    action: str
    priority: int
    reason: str


class DecisionResponse(BaseModel):
    request_id: str
    account_id: str
    decision: Decision
    applied_rules: list[str]


# =============================================================================
# Decision Rules
# =============================================================================

class DecisionRules:
    """
    Simple rule engine for decision making.
    Maps predictions to actions with business logic.
    """
    
    RULES = [
        "confidence_threshold",
        "high_balance_override",
        "contact_limit",
        "account_age_check",
    ]
    
    @staticmethod
    def make_decision(
        prediction: Prediction,
        features: FeatureVector,
        threshold: float = 0.7
    ) -> tuple[Decision, list[str]]:
        """
        Apply rules and return decision.
        Returns (decision, list of applied rules)
        """
        applied_rules = []
        
        # Rule 1: Confidence threshold
        if prediction.confidence < threshold:
            applied_rules.append("confidence_threshold:manual_review")
            return Decision(
                action="ESCALATE_TO_AGENT",
                priority=2,
                reason=f"Low confidence ({prediction.confidence:.2f}), needs human review"
            ), applied_rules
        
        applied_rules.append("confidence_threshold:pass")
        
        # Rule 2: High balance override (>$10k always escalate)
        if features.outstanding_balance > 10000:
            applied_rules.append("high_balance_override:triggered")
            return Decision(
                action="ESCALATE_TO_AGENT",
                priority=1,
                reason=f"High balance account (${features.outstanding_balance:.2f})"
            ), applied_rules
        
        # Rule 3: Contact limit (>15 attempts -> legal)
        if features.contact_attempts > 15:
            applied_rules.append("contact_limit:exceeded")
            return Decision(
                action="INITIATE_LEGAL",
                priority=1,
                reason=f"Contact attempts exceeded ({features.contact_attempts})"
            ), applied_rules
        
        # Map prediction to action
        action_map = {
            "recover": ("SEND_REMINDER", 3, "Predicted recoverable"),
            "escalate": ("CALL_CUSTOMER", 2, "Needs follow-up"),
            "write_off": ("WRITE_OFF", 4, "Predicted unrecoverable"),
            "monitor": ("NO_ACTION", 5, "Continue monitoring"),
        }
        
        action, priority, reason = action_map.get(
            prediction.label,
            ("NO_ACTION", 5, "Unknown prediction")
        )
        
        applied_rules.append(f"prediction_map:{prediction.label}")
        
        return Decision(
            action=action,
            priority=priority,
            reason=reason
        ), applied_rules


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
    logger.info(f"Confidence threshold: {Config.CONFIDENCE_THRESHOLD}")
    logger.info(f"Rules loaded: {len(DecisionRules.RULES)}")
    yield
    logger.info(f"Shutting down {Config.SERVICE_NAME}")


app = FastAPI(
    title="Inflow Decision Engine",
    version=Config.SERVICE_VERSION,
    lifespan=lifespan
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service=Config.SERVICE_NAME,
        version=Config.SERVICE_VERSION,
        rules_loaded=len(DecisionRules.RULES),
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/v1/decide", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest):
    """
    Make a decision based on prediction and features.
    """
    logger.info(f"Processing decision for account: {request.account_id}")
    
    decision, applied_rules = DecisionRules.make_decision(
        prediction=request.prediction,
        features=request.features,
        threshold=Config.CONFIDENCE_THRESHOLD
    )
    
    logger.info(f"Decision: {request.account_id} -> {decision.action} (rules: {applied_rules})")
    
    return DecisionResponse(
        request_id=request.request_id,
        account_id=request.account_id,
        decision=decision,
        applied_rules=applied_rules
    )


@app.get("/v1/rules")
async def list_rules():
    """List available decision rules."""
    return {"rules": DecisionRules.RULES}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
