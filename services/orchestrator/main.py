from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Orchestrator Service")

# --- Mocks ---

class ViabilityClient:
    async def check(self, idea_text: str):
        # Mock logic
        if "fail" in idea_text.lower():
            raise Exception("Viability Service Unavailable")
        return {"score": 0.8, "status": "viable"}

class RiskClient:
    async def scan(self, idea_text: str):
        # Mock logic
        if "risky" in idea_text.lower():
            raise Exception("Risk Service Unavailable")
        return {"level": "low", "flags": []}

class TimingClient:
    async def get_best_time(self):
        # Mock logic
        return {"best_time": "2023-10-27T10:00:00Z"}

# Dependency Injection (Simple Mock)
viability_client = ViabilityClient()
risk_client = RiskClient()
timing_client = TimingClient()

# --- Schemas ---

class IdeaRequest(BaseModel):
    idea_text: str

class IdeaAnalysisResponse(BaseModel):
    viability: dict
    risk: dict
    timing: dict

# --- Endpoints ---

@app.post("/analyze-idea", response_model=IdeaAnalysisResponse)
async def analyze_idea(request: IdeaRequest):
    idea_text = request.idea_text
    response_data = {}

    # 1. Viability Check (Critical)
    try:
        viability = await viability_client.check(idea_text)
        response_data["viability"] = viability
    except Exception as e:
        # Instruction: If Viability fails, return 500 error (Critical dependency).
        raise HTTPException(status_code=500, detail=f"Viability check failed: {str(e)}")

    # 2. Risk Scan (Non-Critical)
    try:
        risk = await risk_client.scan(idea_text)
        response_data["risk"] = risk
    except Exception:
        # Instruction: If Risk fails, set "risk": "UNKNOWN"
        response_data["risk"] = {"status": "UNKNOWN"}

    # 3. Timing (Non-Critical - assuming similar to Risk, though not explicitly specified failure mode, defaulting to safe)
    try:
        timing = await timing_client.get_best_time()
        response_data["timing"] = timing
    except Exception:
        response_data["timing"] = {"status": "UNKNOWN"}

    return response_data

@app.get("/health")
async def health():
    return {"status": "ok"}
