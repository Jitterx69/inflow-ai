"""
Feature Service - Read-only Feature Lookup Stub
Provides feature vectors for inference.
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
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "feature-service", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class Config:
    SERVICE_NAME = "feature-service"
    SERVICE_VERSION = "0.1.0"
    FEATURE_STORE_URL = os.getenv("FEATURE_STORE_URL", "")


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    feature_store_connected: bool = False
    timestamp: str


class FeatureVector(BaseModel):
    account_id: str
    days_past_due: int = 0
    outstanding_balance: float = 0.0
    payment_history_score: float = 0.5
    contact_attempts: int = 0
    last_payment_days_ago: int = 0
    account_age_months: int = 12


class FeatureResponse(BaseModel):
    account_id: str
    features: FeatureVector
    computed_at: str
    cache_hit: bool = False


# =============================================================================
# Mock Data (for dev/testing)
# =============================================================================

MOCK_FEATURES = {
    "ACC001": FeatureVector(
        account_id="ACC001",
        days_past_due=45,
        outstanding_balance=1250.00,
        payment_history_score=0.65,
        contact_attempts=3,
        last_payment_days_ago=60,
        account_age_months=24
    ),
    "ACC002": FeatureVector(
        account_id="ACC002",
        days_past_due=15,
        outstanding_balance=500.00,
        payment_history_score=0.85,
        contact_attempts=1,
        last_payment_days_ago=20,
        account_age_months=36
    ),
    "ACC003": FeatureVector(
        account_id="ACC003",
        days_past_due=90,
        outstanding_balance=5000.00,
        payment_history_score=0.25,
        contact_attempts=10,
        last_payment_days_ago=120,
        account_age_months=48
    ),
}


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
    yield
    logger.info(f"Shutting down {Config.SERVICE_NAME}")


app = FastAPI(
    title="Inflow Feature Service",
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
        feature_store_connected=False,  # TODO: Check feature store
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/v1/features/{account_id}", response_model=FeatureResponse)
async def get_features(account_id: str):
    """
    Get features for a single account.
    STUB: Returns mock data or default features.
    """
    logger.info(f"Getting features for account: {account_id}")
    
    if account_id in MOCK_FEATURES:
        features = MOCK_FEATURES[account_id]
        cache_hit = True
    else:
        # Return default features for unknown accounts
        features = FeatureVector(account_id=account_id)
        cache_hit = False
    
    return FeatureResponse(
        account_id=account_id,
        features=features,
        computed_at=datetime.utcnow().isoformat(),
        cache_hit=cache_hit
    )


@app.post("/v1/features/batch")
async def get_features_batch(account_ids: list[str]):
    """
    Get features for multiple accounts.
    STUB: Returns mock/default data.
    """
    logger.info(f"Getting features for {len(account_ids)} accounts")
    
    results = []
    not_found = []
    
    for account_id in account_ids:
        if account_id in MOCK_FEATURES:
            results.append(FeatureResponse(
                account_id=account_id,
                features=MOCK_FEATURES[account_id],
                computed_at=datetime.utcnow().isoformat(),
                cache_hit=True
            ))
        else:
            results.append(FeatureResponse(
                account_id=account_id,
                features=FeatureVector(account_id=account_id),
                computed_at=datetime.utcnow().isoformat(),
                cache_hit=False
            ))
    
    return {"results": results, "not_found": not_found}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
