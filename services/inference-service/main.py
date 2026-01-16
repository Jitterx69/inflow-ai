"""
Inference Service - Model Loader Stub
Serves ML model predictions.
"""

import os
import logging
import random
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "inference-service", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class Config:
    SERVICE_NAME = "inference-service"
    SERVICE_VERSION = "0.1.0"
    MODEL_PATH = os.getenv("MODEL_PATH", "/models/baseline")
    MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0-stub")


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    model_version: str
    timestamp: str


class FeatureVector(BaseModel):
    account_id: str
    days_past_due: int = 0
    outstanding_balance: float = 0.0
    payment_history_score: float = 0.5
    contact_attempts: int = 0
    last_payment_days_ago: int = 0
    account_age_months: int = 12


class PredictRequest(BaseModel):
    request_id: str
    features: FeatureVector
    model_version: str | None = None


class PredictResponse(BaseModel):
    request_id: str
    prediction: str
    confidence: float
    model_version: str
    inference_time_ms: float


class ExplainResponse(BaseModel):
    request_id: str
    prediction: str
    confidence: float
    feature_importance: list[dict]


# =============================================================================
# Stub Model
# =============================================================================

class StubModel:
    """
    Stub model that returns rule-based predictions.
    Will be replaced with XGBoost in ML baseline phase.
    """
    
    def __init__(self):
        self.version = Config.MODEL_VERSION
        self.loaded = True
    
    def predict(self, features: FeatureVector) -> tuple[str, float]:
        """
        Simple rule-based prediction logic.
        Returns (prediction, confidence)
        """
        # High risk: long overdue + high balance
        if features.days_past_due > 60 and features.outstanding_balance > 2000:
            return "escalate", 0.85
        
        # Write-off candidate: very old debt, low history score
        if features.days_past_due > 120 and features.payment_history_score < 0.3:
            return "write_off", 0.75
        
        # Recoverable: recent, good history
        if features.days_past_due < 30 and features.payment_history_score > 0.7:
            return "recover", 0.90
        
        # Default: monitor
        return "monitor", 0.60
    
    def get_shap_values(self, features: FeatureVector) -> list[dict]:
        """Stub SHAP values for explanation."""
        return [
            {"feature": "days_past_due", "value": features.days_past_due, "shap_value": 0.3, "contribution": "positive"},
            {"feature": "outstanding_balance", "value": features.outstanding_balance, "shap_value": 0.2, "contribution": "positive"},
            {"feature": "payment_history_score", "value": features.payment_history_score, "shap_value": -0.15, "contribution": "negative"},
            {"feature": "contact_attempts", "value": features.contact_attempts, "shap_value": 0.1, "contribution": "positive"},
        ]


# Global model instance
model: StubModel | None = None


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info(f"Starting {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
    logger.info(f"Loading model from {Config.MODEL_PATH}")
    model = StubModel()
    logger.info(f"Model loaded: {model.version}")
    yield
    logger.info(f"Shutting down {Config.SERVICE_NAME}")


app = FastAPI(
    title="Inflow Inference Service",
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
        status="healthy" if model and model.loaded else "unhealthy",
        service=Config.SERVICE_NAME,
        version=Config.SERVICE_VERSION,
        model_loaded=model.loaded if model else False,
        model_version=model.version if model else "none",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/v1/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Run inference on input features.
    STUB: Uses rule-based logic.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start = datetime.utcnow()
    prediction, confidence = model.predict(request.features)
    elapsed = (datetime.utcnow() - start).total_seconds() * 1000
    
    logger.info(f"Prediction: {request.request_id} -> {prediction} ({confidence:.2f})")
    
    return PredictResponse(
        request_id=request.request_id,
        prediction=prediction,
        confidence=confidence,
        model_version=model.version,
        inference_time_ms=elapsed
    )


@app.post("/v1/predict/batch")
async def predict_batch(requests: list[PredictRequest]):
    """Batch inference."""
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start = datetime.utcnow()
    results = []
    
    for req in requests:
        prediction, confidence = model.predict(req.features)
        results.append(PredictResponse(
            request_id=req.request_id,
            prediction=prediction,
            confidence=confidence,
            model_version=model.version,
            inference_time_ms=0
        ))
    
    elapsed = (datetime.utcnow() - start).total_seconds() * 1000
    
    return {"results": results, "total_time_ms": elapsed}


@app.post("/v1/explain", response_model=ExplainResponse)
async def explain(request: PredictRequest):
    """Get prediction explanation with SHAP values."""
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    prediction, confidence = model.predict(request.features)
    shap_values = model.get_shap_values(request.features)
    
    return ExplainResponse(
        request_id=request.request_id,
        prediction=prediction,
        confidence=confidence,
        feature_importance=shap_values
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
