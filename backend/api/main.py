from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
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
from sar.models import AuthenticationRequest, AuthenticationResponse, SARContext
from sar.generator import SARGenerator
from api.middleware import (
    limiter, 
    verify_api_key, 
    add_request_id_middleware, 
    log_request_middleware,
    get_error_response
)

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
            "name": "sar",
            "description": "Suspicious Activity Report generation"
        },
        {
            "name": "demo",
            "description": "Demo and testing endpoints"
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
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom middleware
app.middleware("http")(add_request_id_middleware)
app.middleware("http")(log_request_middleware)

# Initialize orchestrators
orchestrator = UnifiedOrchestrator()
mfa_orchestrator = MFAOrchestrator()
sar_generator = SARGenerator()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
