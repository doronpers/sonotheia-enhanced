from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
import sys
from pathlib import Path
import numpy as np
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from authentication.unified_orchestrator import UnifiedOrchestrator, UnifiedContext
from authentication.mfa_orchestrator import MFAOrchestrator, TransactionContext, AuthenticationFactors
from sar.models import AuthenticationRequest, AuthenticationResponse, SARContext, SARReport, FilingStatus
from sar.generator import SARGenerator
from api.middleware import (
    limiter,
    verify_api_key,
    add_request_id_middleware,
    log_request_middleware,
    add_security_headers_middleware,
    get_error_response
)
from api import session_management, escalation, audit_logging
from api.analyze_call import router as analyze_call_router
from api.jobs import router as jobs_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sonotheia Enhanced API",
    description="""
    # Sonotheia Enhanced Platform
    
    Comprehensive multi-factor voice authentication and SAR reporting system for financial institutions.
    
    ## Features
    
    * **Multi-Factor Authentication**: Advanced voice authentication with deepfake detection
    * **Risk Scoring**: Transaction risk assessment with factor-level analysis
    * **SAR Generation**: Automated Suspicious Activity Report generation
    * **Factor-Level Explainability**: Detailed breakdown of authentication decisions
    
    ## Authentication
    
    API keys are optional for demo/development. Production deployments should use:
    ```
    X-API-Key: your-api-key-here
    ```
    
    ## Rate Limits
    
    * Standard endpoints: 100 requests/minute
    * Authentication endpoints: 50 requests/minute
    * SAR generation: 20 requests/minute
    
    ## Response Format
    
    All responses include:
    * `X-Request-ID`: Unique request identifier for tracking
    * `X-Response-Time`: Processing time in milliseconds
    
    ## Error Codes
    
    * `INVALID_API_KEY`: Invalid or missing API key
    * `RATE_LIMIT_EXCEEDED`: Too many requests
    * `VALIDATION_ERROR`: Invalid request parameters
    * `PROCESSING_ERROR`: Internal processing error
    * `AUTHENTICATION_FAILED`: Authentication validation failed
    """,
    version="1.0.0",
    contact={
        "name": "Sonotheia Support",
        "email": "support@sonotheia.example.com"
    },
    license_info={
        "name": "Proprietary"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "authentication",
            "description": "Multi-factor authentication endpoints"
        },
        {
            "name": "session",
            "description": "Session management for onboarding workflows"
        },
        {
            "name": "escalation",
            "description": "Human-in-the-loop escalation and manual review"
        },
        {
            "name": "audit",
            "description": "Audit logging with compliance tagging"
        },
        {
            "name": "sar",
            "description": "Suspicious Activity Report generation"
        },
        {
            "name": "demo",
            "description": "Demo and testing endpoints"
        },
        {
            "name": "jobs",
            "description": "Async job management for heavy processing tasks"
        }
    ]
)

# CORS Configuration - Improved security with configurable origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    # Add production domains here
    # "https://yourdomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    # Security: Restrict to necessary headers only
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)

# Global exception handler for security
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to prevent information disclosure
    """
    # Log the full error for debugging
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    # Return generic error to client (security: don't leak stack traces)
    import os
    if os.getenv("DEMO_MODE", "true").lower() == "true":
        # In demo mode, provide more details
        detail = {
            "error_code": "INTERNAL_ERROR",
            "message": f"An error occurred: {str(exc)}",
            "type": type(exc).__name__
        }
    else:
        # In production, minimal information
        detail = {
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred. Please contact support."
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=detail
    )

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom middleware (order matters - security headers first)
app.middleware("http")(add_security_headers_middleware)
app.middleware("http")(add_request_id_middleware)
app.middleware("http")(log_request_middleware)

# Initialize orchestrators
orchestrator = UnifiedOrchestrator()
mfa_orchestrator = MFAOrchestrator()
sar_generator = SARGenerator()

# Include routers for new modules
app.include_router(session_management.router)
app.include_router(escalation.router)
app.include_router(audit_logging.router)
app.include_router(analyze_call_router)
app.include_router(jobs_router)

# Request models with enhanced validation and documentation
class AuthRequest(BaseModel):
    """Basic authentication request model for backward compatibility"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_id": "TXN-2024-001",
                "customer_id": "CUST-12345",
                "amount_usd": 50000.00,
                "channel": "wire_transfer",
                "has_consent": True
            }
        }
    )
    
    transaction_id: str = Field(
        ..., 
        description="Unique transaction identifier"
    )
    customer_id: str = Field(
        ..., 
        description="Customer unique identifier"
    )
    amount_usd: float = Field(
        ..., 
        description="Transaction amount in USD",
        gt=0
    )
    channel: str = Field(
        default="wire_transfer", 
        description="Transaction channel"
    )
    has_consent: bool = Field(
        default=True,
        description="Whether customer has provided consent for authentication"
    )


@app.get(
    "/",
    tags=["health"],
    summary="API Information",
    description="Get basic information about the Sonotheia Enhanced API"
)
@limiter.limit("100/minute")
async def root(request: Request):
    """
    Returns basic API information and status.
    
    This endpoint provides an overview of available features and system status.
    """
    return {
        "service": "Sonotheia Enhanced Platform",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Multi-Factor Authentication",
            "Voice Deepfake Detection",
            "SAR Generation",
            "Risk Scoring",
            "Factor-Level Explainability"
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "author": "doronpers"
    }

@app.post(
    "/api/v1/authenticate",
    tags=["authentication"],
    summary="Basic Authentication",
    description="Process basic authentication request with unified orchestrator",
    response_description="Authentication result with decision and factors"
)
@limiter.limit("50/minute")
async def authenticate(
    request: Request,
    auth_request: AuthRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Process authentication request using the unified orchestrator.
    
    This endpoint provides backward compatibility with the basic authentication flow.
    For enhanced multi-factor authentication, use `/api/authenticate` instead.
    
    **Rate Limit**: 50 requests per minute
    
    **Returns**:
    - Authentication decision and supporting factors
    """
    try:
        context = UnifiedContext(
            transaction_id=auth_request.transaction_id,
            customer_id=auth_request.customer_id,
            amount_usd=auth_request.amount_usd,
            channel=auth_request.channel,
            has_consent=auth_request.has_consent
        )
        
        result = await orchestrator.authenticate(context)
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=get_error_response(
                "VALIDATION_ERROR",
                str(e)
            )
        )
    except Exception as e:
        logger.error(f"Authentication processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response(
                "PROCESSING_ERROR",
                "An error occurred during authentication processing"
            )
        )


@app.get(
    "/api/v1/health",
    tags=["health"],
    summary="Health Check",
    description="Check API health status"
)
@limiter.limit("100/minute")
async def health_check(request: Request):
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns system health status and component availability.
    """
    return {
        "status": "healthy", 
        "service": "sonotheia-enhanced",
        "components": {
            "orchestrator": "operational",
            "mfa": "operational",
            "sar": "operational"
        }
    }


@app.post(
    "/api/authenticate",
    response_model=AuthenticationResponse,
    tags=["authentication"],
    summary="Enhanced Multi-Factor Authentication",
    description="Perform comprehensive multi-factor authentication with detailed factor results",
    response_description="Detailed authentication result with all factor evaluations"
)
@limiter.limit("50/minute")
async def authenticate_transaction(
    request: Request,
    auth_request: AuthenticationRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Enhanced multi-factor authentication with detailed factor results.
    
    This endpoint processes multiple authentication factors including:
    - Voice authentication and deepfake detection
    - Device validation
    - Transaction risk scoring
    - Behavioral analysis
    
    **Rate Limit**: 50 requests per minute
    
    **Authentication Decision Types**:
    - `APPROVE`: Transaction approved
    - `DECLINE`: Transaction declined
    - `STEP_UP`: Additional authentication required
    - `MANUAL_REVIEW`: Requires manual review
    
    **Returns**:
    - Comprehensive authentication result with factor-level details
    - Risk score and SAR trigger indicators
    """
    try:
        context = TransactionContext(
            transaction_id=auth_request.transaction_id,
            customer_id=auth_request.customer_id,
            transaction_type=auth_request.channel,
            amount_usd=auth_request.amount_usd,
            destination_country=auth_request.destination_country,
            is_new_beneficiary=auth_request.is_new_beneficiary,
            channel=auth_request.channel
        )
        
        factors = AuthenticationFactors(
            voice={'audio_data': auth_request.voice_sample} if auth_request.voice_sample else None,
            device=auth_request.device_info
        )
        
        result = mfa_orchestrator.authenticate(context, factors)
        return AuthenticationResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=get_error_response(
                "VALIDATION_ERROR",
                str(e)
            )
        )
    except Exception as e:
        logger.error(f"Authentication processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response(
                "PROCESSING_ERROR",
                "An error occurred during authentication processing"
            )
        )


@app.post(
    "/api/sar/generate",
    tags=["sar"],
    summary="Generate SAR Narrative",
    description="Generate Suspicious Activity Report narrative from context data",
    response_description="SAR narrative with quality validation"
)
@limiter.limit("20/minute")
async def generate_sar(
    request: Request,
    context: SARContext,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Generate SAR (Suspicious Activity Report) narrative from context data.
    
    This endpoint generates a comprehensive SAR narrative based on the provided
    context, including transaction details, risk factors, and authentication results.
    
    **Rate Limit**: 20 requests per minute (SAR generation is resource-intensive)
    
    **Returns**:
    - Generated SAR narrative
    - Quality validation results
    - Compliance indicators
    """
    try:
        narrative = sar_generator.generate_sar(context)
        validation = sar_generator.validate_sar_quality(narrative)
        
        return {
            'narrative': narrative,
            'validation': validation,
            'context_id': context.transaction_id if hasattr(context, 'transaction_id') else None
        }
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=get_error_response(
                "VALIDATION_ERROR",
                str(e)
            )
        )
    except Exception as e:
        logger.error(f"SAR generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response(
                "PROCESSING_ERROR",
                "An error occurred during SAR generation"
            )
        )


@app.get(
    "/api/demo/waveform/{sample_id}",
    tags=["demo"],
    summary="Get Demo Waveform Data",
    description="Return demo waveform data for visualization testing",
    response_description="Waveform data with segments"
)
@limiter.limit("100/minute")
async def get_demo_waveform(request: Request, sample_id: str):
    """
    Return demo waveform data for visualization.
    
    This endpoint provides sample waveform data for testing visualization
    components and UI development.
    
    **Parameters**:
    - `sample_id`: Identifier for the demo sample
    
    **Returns**:
    - x/y coordinates for waveform plot
    - Annotated segments (genuine vs synthetic)
    - Confidence scores
    """
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
        "sample_id": sample_id,
        "sample_rate": 16000,
        "duration_seconds": 4.0
    }


# Dashboard endpoints
@app.get(
    "/api/dashboard/status",
    tags=["demo"],
    summary="Dashboard Status",
    description="Get system status and metrics for dashboard"
)
@limiter.limit("100/minute")
async def get_dashboard_status(request: Request):
    """Get system status and metrics for dashboard"""
    return {
        "totalTests": 15,
        "passedTests": 12,
        "failedTests": 2,
        "uptime": "99.9%",
        "lastUpdate": datetime.now().isoformat(),
        "systemHealth": "operational"
    }


@app.get(
    "/api/dashboard/module-params",
    tags=["demo"],
    summary="Module Parameters",
    description="Get current module parameters"
)
@limiter.limit("100/minute")
async def get_module_parameters(request: Request):
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


@app.post(
    "/api/dashboard/module-params",
    tags=["demo"],
    summary="Update Module Parameters",
    description="Update module parameters"
)
@limiter.limit("50/minute")
async def update_module_parameters(request: Request, params: Dict):
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


def _get_test_results_data():
    """Internal function to get test results data"""
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


@app.get(
    "/api/dashboard/test-results",
    tags=["demo"],
    summary="Test Results",
    description="Get test execution results"
)
@limiter.limit("100/minute")
async def get_test_results(request: Request):
    """Get test execution results"""
    return _get_test_results_data()


@app.post(
    "/api/dashboard/run-tests",
    tags=["demo"],
    summary="Run Tests",
    description="Execute test suite and return results"
)
@limiter.limit("20/minute")
async def run_tests(request: Request):
    """Execute test suite and return results"""
    try:
        # Simulate test execution
        # In a real implementation, this would run actual tests
        results = _get_test_results_data()
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
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
