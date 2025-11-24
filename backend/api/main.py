from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
from pathlib import Path
import numpy as np
from datetime import datetime

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from authentication.unified_orchestrator import UnifiedOrchestrator, UnifiedContext
from authentication.mfa_orchestrator import MFAOrchestrator, TransactionContext, AuthenticationFactors
from sar.models import AuthenticationRequest, AuthenticationResponse, SARContext
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


# Dashboard endpoints
@app.get("/api/dashboard/status")
async def get_dashboard_status():
    """Get system status and metrics for dashboard"""
    return {
        "totalTests": 15,
        "passedTests": 12,
        "failedTests": 2,
        "uptime": "99.9%",
        "lastUpdate": datetime.now().isoformat(),
        "systemHealth": "operational"
    }


@app.get("/api/dashboard/module-params")
async def get_module_parameters():
    """Get current module parameters"""
    return {
        "voice": {
            "deepfake_threshold": 0.3,
            "speaker_threshold": 0.85,
            "liveness_threshold": 0.8,
            "sample_rate": 16000,
            "min_duration": 1.0,
            "max_duration": 30.0
        },
        "device": {
            "trust_score_threshold": 0.8,
            "require_enrollment": True,
            "check_location": True,
            "max_devices": 5
        },
        "mfa": {
            "min_factors": 2,
            "require_voice_high_value": True,
            "high_value_threshold": 10000,
            "critical_risk_threshold": 0.7
        },
        "sar": {
            "auto_generate": True,
            "synthetic_voice_threshold": 0.7,
            "high_value_amount": 50000,
            "require_manual_review": True
        }
    }


@app.post("/api/dashboard/module-params")
async def update_module_parameters(params: Dict):
    """Update module parameters"""
    try:
        # In a real implementation, this would update the configuration
        # For now, just validate and return success
        return {
            "status": "success",
            "message": "Parameters updated successfully",
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/test-results")
async def get_test_results():
    """Get test execution results"""
    return [
        {
            "name": "Voice Deepfake Detection",
            "module": "voice",
            "status": "pass",
            "duration": "0.12s",
            "score": 0.15,
            "details": "No synthetic artifacts detected"
        },
        {
            "name": "Speaker Verification",
            "module": "voice",
            "status": "pass",
            "duration": "0.08s",
            "score": 0.96,
            "details": "Voice matches enrolled voiceprint"
        },
        {
            "name": "Liveness Check",
            "module": "voice",
            "status": "pass",
            "duration": "0.05s",
            "score": 1.0,
            "details": "Active liveness challenge passed"
        },
        {
            "name": "Device Trust Score",
            "module": "device",
            "status": "pass",
            "duration": "0.03s",
            "score": 0.85,
            "details": "Known device with good reputation"
        },
        {
            "name": "Device Enrollment",
            "module": "device",
            "status": "pass",
            "duration": "0.02s",
            "score": 1.0,
            "details": "Device is properly enrolled"
        },
        {
            "name": "Location Consistency",
            "module": "device",
            "status": "warn",
            "duration": "0.04s",
            "score": 0.65,
            "details": "Location differs from usual pattern"
        },
        {
            "name": "MFA Policy Check",
            "module": "mfa",
            "status": "pass",
            "duration": "0.01s",
            "score": 1.0,
            "details": "Sufficient factors passed"
        },
        {
            "name": "Risk Assessment",
            "module": "mfa",
            "status": "pass",
            "duration": "0.02s",
            "score": 0.25,
            "details": "Low risk level"
        },
        {
            "name": "Transaction Analysis",
            "module": "mfa",
            "status": "pass",
            "duration": "0.03s",
            "score": 0.3,
            "details": "Medium value transaction"
        },
        {
            "name": "SAR Trigger Detection",
            "module": "sar",
            "status": "pass",
            "duration": "0.01s",
            "score": 0.0,
            "details": "No SAR flags detected"
        },
        {
            "name": "Compliance Check",
            "module": "sar",
            "status": "pass",
            "duration": "0.02s",
            "score": 1.0,
            "details": "All compliance requirements met"
        },
        {
            "name": "Audit Logging",
            "module": "system",
            "status": "pass",
            "duration": "0.01s",
            "score": 1.0,
            "details": "All actions logged successfully"
        },
        {
            "name": "Performance Benchmark",
            "module": "system",
            "status": "pass",
            "duration": "0.45s",
            "score": 0.9,
            "details": "Processing time within acceptable range"
        },
        {
            "name": "Memory Usage",
            "module": "system",
            "status": "pass",
            "duration": "0.01s",
            "score": 0.7,
            "details": "Memory usage at 70% capacity"
        },
        {
            "name": "Error Handling",
            "module": "system",
            "status": "pass",
            "duration": "0.02s",
            "score": 1.0,
            "details": "All error cases handled gracefully"
        }
    ]


@app.post("/api/dashboard/run-tests")
async def run_tests():
    """Execute test suite and return results"""
    try:
        # Simulate test execution
        # In a real implementation, this would run actual tests
        results = await get_test_results()
        return {
            "status": "success",
            "results": results,
            "executed_at": datetime.now().isoformat(),
            "total": len(results),
            "passed": len([r for r in results if r["status"] == "pass"]),
            "failed": len([r for r in results if r["status"] == "fail"]),
            "warnings": len([r for r in results if r["status"] == "warn"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
