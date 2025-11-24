from fastapi import FastAPI, HTTPException, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from authentication.unified_orchestrator import UnifiedOrchestrator, UnifiedContext
from authentication.mfa_orchestrator import MFAOrchestrator, TransactionContext, AuthenticationFactors
from sar.models import AuthenticationRequest, AuthenticationResponse, SARContext, SARReport, FilingStatus
from sar.generator import SARGenerator

app = FastAPI(
    title="Sonotheia Enhanced API",
    description="Multi-factor voice authentication & SAR reporting system",
    version="1.0.0"
)

# CORS for development - allow all common React ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrators
orchestrator = UnifiedOrchestrator()
mfa_orchestrator = MFAOrchestrator()
sar_generator = SARGenerator()

# Request models (keeping backward compatibility)
class AuthRequest(BaseModel):
    transaction_id: str
    customer_id: str
    amount_usd: float
    channel: str = "wire_transfer"
    has_consent: bool = True

@app.get("/")
async def root():
    return {
        "service": "Sonotheia Enhanced Platform",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Multi-Factor Authentication",
            "Voice Deepfake Detection",
            "SAR Generation",
            "Risk Scoring"
        ],
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
    return {"status": "healthy", "service": "sonotheia-enhanced"}


@app.post("/api/authenticate", response_model=AuthenticationResponse)
async def authenticate_transaction(request: AuthenticationRequest):
    """Enhanced multi-factor authentication with detailed factor results"""
    try:
        context = TransactionContext(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            transaction_type=request.channel,
            amount_usd=request.amount_usd,
            destination_country=request.destination_country,
            is_new_beneficiary=request.is_new_beneficiary,
            channel=request.channel
        )
        
        factors = AuthenticationFactors(
            voice={'audio_data': request.voice_sample} if request.voice_sample else None,
            device=request.device_info
        )
        
        result = mfa_orchestrator.authenticate(context, factors)
        return AuthenticationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sar/generate")
async def generate_sar(context: SARContext):
    """Generate SAR narrative from context data"""
    try:
        narrative = sar_generator.generate_sar(context)
        validation = sar_generator.validate_sar_quality(narrative)
        
        return {
            'narrative': narrative,
            'validation': validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sar/reports", response_model=SARReport)
async def create_sar_report(context: SARContext):
    """Create a complete SAR report with intelligence analysis"""
    try:
        report = sar_generator.create_sar_report(context)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sar/reports", response_model=List[SARReport])
async def list_sar_reports(
    status: Optional[str] = Query(None, description="Filter by filing status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of reports to return")
):
    """List SAR reports with optional filtering"""
    try:
        reports = sar_generator.list_reports(status=status, limit=limit)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sar/reports/{sar_id}", response_model=SARReport)
async def get_sar_report(sar_id: str):
    """Get a specific SAR report by ID"""
    try:
        report = sar_generator.get_report(sar_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"SAR report {sar_id} not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sar/reports/{sar_id}/export")
async def export_sar_report(sar_id: str, format: str = Query("txt", pattern="^(txt|json)$")):
    """Export SAR report in various formats"""
    try:
        report = sar_generator.get_report(sar_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"SAR report {sar_id} not found")
        
        if format == "json":
            return report
        else:  # txt format
            return Response(
                content=report.narrative,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f'attachment; filename="{sar_id}.txt"'
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo/waveform/{sample_id}")
async def get_demo_waveform(sample_id: str):
    """Return demo waveform data for visualization"""
    # Generate demo waveform data
    x = np.linspace(0, 4, 1000)
    y = np.sin(2 * np.pi * x) * np.exp(-x/2)
    
    return {
        "x": x.tolist(),
        "y": y.tolist(),
        "segments": [
            {
                "start": 0.0,
                "end": 2.0,
                "type": "genuine",
                "label": "Genuine",
                "confidence": 0.95
            },
            {
                "start": 2.0,
                "end": 4.0,
                "type": "synthetic",
                "label": "Synthetic",
                "confidence": 0.88
            }
        ],
        "sample_id": sample_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
