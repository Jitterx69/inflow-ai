"""
LLM Gateway Service
CRITICAL: LLMs are ADVISORY ONLY - they NEVER make final decisions.
"""

import os
import json
import logging
import time
from datetime import datetime, date
from contextlib import asynccontextmanager
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "llm-service", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class Config:
    SERVICE_NAME = "llm-service"
    SERVICE_VERSION = "0.1.0"
    DAILY_TOKEN_LIMIT = int(os.getenv("DAILY_TOKEN_LIMIT", "1000000"))
    MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", "4000"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1000"))
    REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
    FALLBACK_ENABLED = os.getenv("FALLBACK_ENABLED", "true").lower() == "true"


# =============================================================================
# Token Tracking
# =============================================================================

class TokenTracker:
    """Tracks token usage for cost control."""
    
    def __init__(self):
        self._daily_tokens = 0
        self._hourly_tokens = 0
        self._current_date = date.today()
        self._current_hour = datetime.now().hour
    
    def _reset_if_needed(self):
        """Reset counters on new day/hour."""
        now = datetime.now()
        if now.date() != self._current_date:
            self._daily_tokens = 0
            self._current_date = now.date()
        if now.hour != self._current_hour:
            self._hourly_tokens = 0
            self._current_hour = now.hour
    
    def can_use(self, tokens: int) -> bool:
        """Check if token budget allows usage."""
        self._reset_if_needed()
        return (
            self._daily_tokens + tokens <= Config.DAILY_TOKEN_LIMIT and
            self._hourly_tokens + tokens <= Config.DAILY_TOKEN_LIMIT // 10
        )
    
    def record_usage(self, input_tokens: int, output_tokens: int):
        """Record token usage."""
        total = input_tokens + output_tokens
        self._daily_tokens += total
        self._hourly_tokens += total
        logger.info(f"Token usage: +{total} (daily: {self._daily_tokens})")
    
    def get_usage(self) -> dict:
        """Get current usage stats."""
        self._reset_if_needed()
        return {
            "daily_tokens": self._daily_tokens,
            "daily_limit": Config.DAILY_TOKEN_LIMIT,
            "daily_percent": (self._daily_tokens / Config.DAILY_TOKEN_LIMIT) * 100
        }


token_tracker = TokenTracker()


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    tokens_remaining: int


class LLMRequest(BaseModel):
    request_id: str
    use_case: str  # summarization, explanation, suggestion
    context: str
    query: str
    max_tokens: Optional[int] = None


class LLMResponse(BaseModel):
    request_id: str
    use_case: str
    response: str
    tokens_used: int
    is_fallback: bool
    advisory_only: bool = True  # Always true - LLMs don't make decisions


# =============================================================================
# LLM Client (Stub)
# =============================================================================

class LLMClient:
    """
    LLM client stub.
    In production, this would call OpenAI/Anthropic APIs.
    """
    
    ALLOWED_USE_CASES = ["summarization", "explanation", "suggestion"]
    
    async def generate(
        self,
        use_case: str,
        context: str,
        query: str,
        max_tokens: int = 500
    ) -> tuple[str, int]:
        """
        Generate LLM response.
        Returns (response, tokens_used)
        """
        if use_case not in self.ALLOWED_USE_CASES:
            raise ValueError(f"Invalid use case: {use_case}")
        
        # Simulate LLM call
        # In production: call OpenAI/Anthropic API
        
        if use_case == "summarization":
            response = f"Summary: Based on the provided context about {context[:50]}..., the key points are: 1) Account status overview, 2) Payment history analysis, 3) Recommended next steps."
        elif use_case == "explanation":
            response = f"Explanation: The model prediction is based on several factors: days past due, outstanding balance, and payment history. The primary driver is the payment history score."
        else:  # suggestion
            response = f"Suggestion (ADVISORY ONLY): Based on the analysis, consider reaching out to the customer within the next 48 hours. Note: This is a suggestion only - final decision requires human review."
        
        tokens_used = len(response.split()) * 2  # Rough estimate
        
        return response, tokens_used


llm_client = LLMClient()


# =============================================================================
# Fallback Logic
# =============================================================================

def get_classical_fallback(use_case: str, context: str) -> str:
    """Returns classical (non-LLM) response when LLM fails."""
    logger.warning(f"Using classical fallback for use_case={use_case}")
    
    if use_case == "summarization":
        return "Summary unavailable. Please refer to the raw data."
    elif use_case == "explanation":
        return "Explanation: Prediction based on standard feature weights. See model documentation for details."
    else:
        return "Suggestion unavailable. Please follow standard operating procedures."


# =============================================================================
# Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
    logger.info(f"Daily token limit: {Config.DAILY_TOKEN_LIMIT}")
    logger.info("⚠️ IMPORTANT: LLM outputs are ADVISORY ONLY")
    yield
    logger.info(f"Shutting down {Config.SERVICE_NAME}")


app = FastAPI(
    title="Inflow LLM Service",
    version=Config.SERVICE_VERSION,
    description="Advisory AI service - outputs are suggestions only",
    lifespan=lifespan
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check."""
    usage = token_tracker.get_usage()
    return HealthResponse(
        status="healthy",
        service=Config.SERVICE_NAME,
        version=Config.SERVICE_VERSION,
        tokens_remaining=Config.DAILY_TOKEN_LIMIT - usage["daily_tokens"]
    )


@app.post("/v1/generate", response_model=LLMResponse)
async def generate(request: LLMRequest):
    """
    Generate LLM response.
    CRITICAL: Response is ADVISORY ONLY.
    """
    logger.info(f"LLM request: {request.request_id} use_case={request.use_case}")
    
    # Validate use case
    if request.use_case not in LLMClient.ALLOWED_USE_CASES:
        raise HTTPException(400, f"Invalid use case. Allowed: {LLMClient.ALLOWED_USE_CASES}")
    
    max_tokens = min(request.max_tokens or Config.MAX_OUTPUT_TOKENS, Config.MAX_OUTPUT_TOKENS)
    
    # Check token budget
    estimated_tokens = len(request.context.split()) + len(request.query.split()) + max_tokens
    if not token_tracker.can_use(estimated_tokens):
        logger.warning(f"Token budget exceeded for {request.request_id}")
        # Return fallback
        return LLMResponse(
            request_id=request.request_id,
            use_case=request.use_case,
            response=get_classical_fallback(request.use_case, request.context),
            tokens_used=0,
            is_fallback=True,
            advisory_only=True
        )
    
    try:
        response, tokens_used = await llm_client.generate(
            use_case=request.use_case,
            context=request.context,
            query=request.query,
            max_tokens=max_tokens
        )
        
        token_tracker.record_usage(estimated_tokens - max_tokens, tokens_used)
        
        return LLMResponse(
            request_id=request.request_id,
            use_case=request.use_case,
            response=response,
            tokens_used=tokens_used,
            is_fallback=False,
            advisory_only=True
        )
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        
        if Config.FALLBACK_ENABLED:
            return LLMResponse(
                request_id=request.request_id,
                use_case=request.use_case,
                response=get_classical_fallback(request.use_case, request.context),
                tokens_used=0,
                is_fallback=True,
                advisory_only=True
            )
        raise HTTPException(503, "LLM service unavailable")


@app.get("/v1/usage")
async def get_usage():
    """Get current token usage stats."""
    return token_tracker.get_usage()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
