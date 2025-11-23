from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from authentication.unified_orchestrator import UnifiedOrchestrator, UnifiedContext

app = FastAPI(
    title="Sonotheia Unified API",
    description="Forensic audio authentication platform by doronpers",
    version="0.1.0"
)

# CORS for development - allow all common React ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = UnifiedOrchestrator()

# Request models
class AuthRequest(BaseModel):
    transaction_id: str
    customer_id: str
    amount_usd: float
    channel: str = "wire_transfer"
    has_consent: bool = True

@app.get("/")
async def root():
    return {
        "service": "Sonotheia Unified Platform",
        "version": "0.1.0",
        "status": "operational",
        "author": "doronpers"
    }

@app.post("/api/v1/authenticate")
async def authenticate(request: AuthRequest):
    """Process authentication request"""
    try:
        context = UnifiedContext(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            amount_usd=request.amount_usd,
            channel=request.channel,
            has_consent=request.has_consent
        )
        
        result = await orchestrator.authenticate(context)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "sonotheia-unified"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
