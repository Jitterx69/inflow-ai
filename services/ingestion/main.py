"""
Ingestion Service - Kafka Consumer Stub
Consumes events from Kafka and forwards to feature pipeline.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "ingestion", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

from confluent_kafka import Producer
import json


# Initialize Producer (Global for simplicity, or in lifespan)
producer_conf = {'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")}
# In real app, producer should be created in lifespan
try:
    producer = Producer(producer_conf)
except Exception as e:
    logger.error(f"Failed to create producer: {e}")
    producer = None

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")



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


@app.post("/webhooks/instagram")
async def instagram_webhook(request: dict, x_hub_signature: str | None = None):
    """
    Receives Instagram webhooks.
    """
    # 1. Signature Verification (Simplified Stub)
    # In reality: hmac.new(app_secret, request_body, hashlib.sha256)
    if not x_hub_signature and os.getenv("ENV") == "prod":
        logger.warning("Missing signature")
        # raise HTTPException(403, "Missing signature")
    
    logger.info(f"Received Instagram webhook: {request}")

    # 2. Push to Kafka
    if producer:
        try:
            producer.produce(
                "raw.social.events",
                key=str(request.get("object", "instagram")),
                value=json.dumps(request),
                callback=delivery_report
            )
            producer.poll(0)
            return {"status": "accepted"}
        except Exception as e:
            logger.error(f"Failed to produce to Kafka: {e}")
            return {"status": "error", "detail": str(e)}
    
    return {"status": "accepted (kafka unavailable)"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
