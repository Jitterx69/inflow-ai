from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import httpx
import os

app = FastAPI(title="API Gateway")
security = HTTPBasic()

# Mock Credentials (in real app, use auth service or db)
USERNAME = os.getenv("AUTH_USER", "admin")
PASSWORD = os.getenv("AUTH_PASS", "secret")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


# Service URLs (Env vars with defaults for local dev)
STUDIO_URL = os.getenv("STUDIO_URL", "http://localhost:8001")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8002")
INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8003")

client = httpx.AsyncClient()

# Helper for reverse proxy
async def reverse_proxy(target_url: str, request: Request):
    url = f"{target_url}{request.url.path}"
    # Strip the gateway prefix if needed, or assume backend paths match
    # For this implementation, we'll map prefixes strictly
    
    # Simple mapping strategy:
    # Gateway: /api/v1/studio/drafts -> Studio: /drafts
    # Gateway: /api/v1/analyze -> Orchestrator: /analyze-idea
    # Gateway: /webhooks/instagram -> Ingestion: /webhooks/instagram
    
    if request.url.path.startswith("/api/v1/studio"):
        backend_path = request.url.path.replace("/api/v1/studio", "")
        url = f"{STUDIO_URL}{backend_path}"
    elif request.url.path.startswith("/api/v1/analyze"): # Logic matches endpoint
        backend_path = request.url.path.replace("/api/v1", "") # Orchestrator base is /
        url = f"{ORCHESTRATOR_URL}{backend_path}"
    elif request.url.path.startswith("/webhooks"):
        url = f"{INGESTION_URL}{request.url.path}"

    try:
        content = await request.body()
        req_headers = dict(request.headers)
        # Avoid host header conflict
        req_headers.pop("host", None)
        
        rp_req = client.build_request(
            request.method,
            url,
            headers=req_headers,
            content=content
        )
        rp_resp = await client.send(rp_req)
        
        return Response(
            content=rp_resp.content,
            status_code=rp_resp.status_code,
            headers=dict(rp_resp.headers)
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")

# --- Routes ---

@app.api_route("/api/v1/studio/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], dependencies=[Depends(verify_credentials)])
async def studio_proxy(path: str, request: Request):
    return await reverse_proxy(STUDIO_URL, request)

@app.post("/api/v1/analyze", dependencies=[Depends(verify_credentials)])
async def analyze_proxy(request: Request):
    return await reverse_proxy(ORCHESTRATOR_URL, request)

@app.api_route("/webhooks/{path:path}", methods=["POST"])
async def webhook_proxy(path: str, request: Request):
    return await reverse_proxy(INGESTION_URL, request)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()
