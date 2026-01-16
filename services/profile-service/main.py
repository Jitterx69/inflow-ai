"""
Profile Service - User/Entity Profiles with Memory
Privacy-first design with explainable, erasable memory.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "profile-service", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class Config:
    SERVICE_NAME = "profile-service"
    SERVICE_VERSION = "0.1.0"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
    MEMORY_RETENTION_DAYS = int(os.getenv("MEMORY_RETENTION_DAYS", "90"))


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ProfileSignal(BaseModel):
    """Aggregated signal - never raw personal data."""
    signal_type: str  # engagement, risk, response_rate, etc.
    value: float
    confidence: float
    computed_at: str


class SessionMemory(BaseModel):
    """Short-term session memory."""
    session_id: str
    account_id: str
    interactions: list[dict]
    created_at: str
    expires_at: str


class LongTermMemory(BaseModel):
    """Long-term aggregated signals - no raw data."""
    account_id: str
    signals: list[ProfileSignal]
    last_updated: str


class Profile(BaseModel):
    account_id: str
    session_memory: Optional[SessionMemory] = None
    long_term_memory: Optional[LongTermMemory] = None
    personalization_enabled: bool = True


# =============================================================================
# Memory Store (Stub)
# =============================================================================

class MemoryStore:
    """
    Memory store stub - would use Redis in production.
    All data is aggregated signals, never raw personal data.
    """
    
    def __init__(self):
        self._sessions: dict[str, SessionMemory] = {}
        self._long_term: dict[str, LongTermMemory] = {}
    
    async def get_session(self, account_id: str) -> Optional[SessionMemory]:
        """Get current session memory."""
        return self._sessions.get(account_id)
    
    async def create_session(self, account_id: str, session_id: str) -> SessionMemory:
        """Create new session."""
        now = datetime.utcnow()
        session = SessionMemory(
            session_id=session_id,
            account_id=account_id,
            interactions=[],
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=Config.SESSION_TTL_HOURS)).isoformat()
        )
        self._sessions[account_id] = session
        return session
    
    async def add_interaction(self, account_id: str, interaction: dict):
        """Add interaction to session memory."""
        if account_id in self._sessions:
            self._sessions[account_id].interactions.append({
                **interaction,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def get_long_term(self, account_id: str) -> Optional[LongTermMemory]:
        """Get long-term aggregated signals."""
        return self._long_term.get(account_id)
    
    async def update_signals(self, account_id: str, signals: list[ProfileSignal]):
        """Update long-term signals (aggregated only)."""
        self._long_term[account_id] = LongTermMemory(
            account_id=account_id,
            signals=signals,
            last_updated=datetime.utcnow().isoformat()
        )
    
    async def delete_memory(self, account_id: str) -> bool:
        """Delete all memory for an account (GDPR compliance)."""
        deleted = False
        if account_id in self._sessions:
            del self._sessions[account_id]
            deleted = True
        if account_id in self._long_term:
            del self._long_term[account_id]
            deleted = True
        logger.info(f"Deleted memory for account: {account_id}")
        return deleted
    
    async def explain_memory(self, account_id: str) -> dict:
        """Explain what memory is stored (transparency)."""
        session = self._sessions.get(account_id)
        long_term = self._long_term.get(account_id)
        
        return {
            "account_id": account_id,
            "has_session_memory": session is not None,
            "session_interaction_count": len(session.interactions) if session else 0,
            "has_long_term_memory": long_term is not None,
            "signal_types": [s.signal_type for s in long_term.signals] if long_term else [],
            "data_retention_days": Config.MEMORY_RETENTION_DAYS,
            "note": "Only aggregated signals are stored, never raw personal data"
        }


memory_store = MemoryStore()


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
    logger.info("Memory is explainable and erasable")
    yield
    logger.info(f"Shutting down {Config.SERVICE_NAME}")


app = FastAPI(
    title="Inflow Profile Service",
    version=Config.SERVICE_VERSION,
    lifespan=lifespan
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service=Config.SERVICE_NAME,
        version=Config.SERVICE_VERSION
    )


@app.get("/v1/profile/{account_id}", response_model=Profile)
async def get_profile(account_id: str):
    """Get profile with memory."""
    session = await memory_store.get_session(account_id)
    long_term = await memory_store.get_long_term(account_id)
    
    return Profile(
        account_id=account_id,
        session_memory=session,
        long_term_memory=long_term,
        personalization_enabled=True
    )


@app.post("/v1/profile/{account_id}/interaction")
async def record_interaction(account_id: str, interaction: dict):
    """Record an interaction in session memory."""
    session = await memory_store.get_session(account_id)
    if not session:
        session = await memory_store.create_session(account_id, f"sess_{account_id}")
    
    await memory_store.add_interaction(account_id, interaction)
    return {"status": "recorded"}


@app.delete("/v1/profile/{account_id}")
async def delete_profile(account_id: str):
    """Delete all memory for an account (GDPR right to erasure)."""
    deleted = await memory_store.delete_memory(account_id)
    return {"account_id": account_id, "deleted": deleted}


@app.get("/v1/profile/{account_id}/explain")
async def explain_profile(account_id: str):
    """Explain what data is stored (transparency)."""
    return await memory_store.explain_memory(account_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
