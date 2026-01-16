"""
Ingestion Service - Kafka Consumer Stub
Consumes events from Kafka and forwards to feature pipeline.
"""

import os
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "ingestion", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration (env vars only)
# =============================================================================

class Config:
    SERVICE_NAME = "ingestion"
    SERVICE_VERSION = "0.1.0"
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "inflow-events")
    KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "ingestion-group")


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    kafka_connected: bool = False
    timestamp: str


class IngestEvent(BaseModel):
    event_id: str
    event_type: str
    account_id: str
    payload: dict
    timestamp: int | None = None


class IngestResponse(BaseModel):
    event_id: str
    success: bool
    message: str


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
    logger.info(f"Kafka bootstrap: {Config.KAFKA_BOOTSTRAP_SERVERS}")
    # TODO: Initialize Kafka consumer in P1.4
    yield
    # Shutdown
    logger.info(f"Shutting down {Config.SERVICE_NAME}")


app = FastAPI(
    title="Inflow Ingestion Service",
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
        kafka_connected=False,  # TODO: Check Kafka connection
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest_event(event: IngestEvent):
    """
    Ingest a single event.
    STUB: Logs the event, does not actually process.
    """
    logger.info(f"Received event: {event.event_id} type={event.event_type} account={event.account_id}")
    
    # TODO: Forward to Kafka / feature pipeline
    return IngestResponse(
        event_id=event.event_id,
        success=True,
        message="Event received (stub - not processed)"
    )


@app.post("/v1/ingest/batch")
async def ingest_batch(events: list[IngestEvent]):
    """
    Ingest multiple events.
    STUB: Logs count, does not actually process.
    """
    logger.info(f"Received batch of {len(events)} events")
    
    return {
        "received": len(events),
        "processed": 0,
        "message": "Batch received (stub - not processed)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
