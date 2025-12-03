"""
Detection API Router

API endpoints for the 6-stage detection pipeline.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, File, UploadFile, Request, Depends, status
from pydantic import BaseModel, Field

from api.middleware import limiter, verify_api_key, get_error_response
from api.validation import SensorResult
from backend.sensors.utils import load_and_preprocess_audio
from detection import get_pipeline, convert_numpy_types

logger = logging.getLogger(__name__)

# Constants
MAX_AUDIO_FILE_SIZE_MB = 800
MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024

router = APIRouter(prefix="/api/detect", tags=["detection"])


# Request/Response Models
class DetectionRequest(BaseModel):
    """Detection request with audio data or reference."""

    audio_base64: Optional[str] = Field(
        None, description="Base64-encoded audio data"
    )
    audio_url: Optional[str] = Field(
        None, description="URL to audio file (not implemented)"
    )
    quick_mode: bool = Field(
        False, description="Run quick detection (stages 1-3 only)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quick_mode": False,
            }
        }


class DetectionResponse(BaseModel):
    """Detection pipeline response."""

    success: bool = Field(..., description="Whether detection succeeded")
    job_id: str = Field(..., description="Unique job identifier")
    detection_score: float = Field(..., ge=0, le=1, description="Spoof detection score")
    is_spoof: bool = Field(..., description="Whether audio is classified as spoof")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    decision: str = Field(..., description="Detection decision")
    quick_mode: bool = Field(..., description="Whether quick mode was used")
    demo_mode: bool = Field(..., description="Whether demo mode is active")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    timestamp: str = Field(..., description="Processing timestamp")
    explanation: Optional[dict] = Field(None, description="Detection explanation")


class JobStatusResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: str
    progress: float
    current_stage: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


@router.post(
    "",
    response_model=DetectionResponse,
    summary="Run Full Detection Pipeline",
    description="Run the complete 6-stage detection pipeline on uploaded audio",
)
@limiter.limit("30/minute")
async def detect_full(
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyze"),
    quick_mode: bool = False,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Run full detection pipeline on uploaded audio.

    This endpoint processes audio through all 6 stages:
    1. Feature Extraction
    2. Temporal Analysis
    3. Artifact Detection
    4. RawNet3 Neural Network
    5. Fusion Engine
    6. Explainability

    **Rate Limit**: 30 requests per minute

    **File Size**: Max 800MB

    **Supported Formats**: WAV, MP3, FLAC, OGG
    """
    try:
        # Read audio file
        import io
        audio_bytes = await file.read()
        
        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Empty audio file"),
            )

        if len(audio_bytes) > MAX_AUDIO_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=get_error_response(
                    "FILE_TOO_LARGE", f"Audio file exceeds {MAX_AUDIO_FILE_SIZE_MB}MB limit"
                ),
            )

        # Preprocess
        audio_io = io.BytesIO(audio_bytes)
        audio_array, sr = load_and_preprocess_audio(audio_io)

        # Get pipeline and run detection
        pipeline = get_pipeline()
        result = pipeline.detect(audio_array, quick_mode=quick_mode)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=get_error_response(
                    "PROCESSING_ERROR",
                    result.get("error", "Detection failed"),
                ),
            )

        return DetectionResponse(
            success=True,
            job_id=result.get("job_id", ""),
            detection_score=result.get("detection_score", 0.5),
            is_spoof=result.get("is_spoof", False),
            confidence=result.get("confidence", 0.0),
            decision=result.get("decision", "UNCERTAIN"),
            quick_mode=result.get("quick_mode", False),
            demo_mode=result.get("demo_mode", True),
            duration_seconds=result.get("duration_seconds"),
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            explanation=result.get("explanation"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", str(e)),
        )


@router.post(
    "/quick",
    response_model=DetectionResponse,
    summary="Run Quick Detection",
    description="Run lightweight detection using only acoustic analysis (stages 1-3)",
)
@limiter.limit("60/minute")
async def detect_quick(
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyze"),
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Run quick detection (stages 1-3 only).

    This is a faster, lightweight detection that only runs:
    1. Feature Extraction
    2. Temporal Analysis
    3. Artifact Detection

    Suitable for initial screening before full analysis.

    **Rate Limit**: 60 requests per minute
    """
    try:
        audio_bytes = await file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Empty audio file"),
            )

        # Preprocess
        import io
        audio_io = io.BytesIO(audio_bytes)
        audio_array, sr = load_and_preprocess_audio(audio_io)

        pipeline = get_pipeline()
        result = pipeline.detect(audio_array, quick_mode=True)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=get_error_response(
                    "PROCESSING_ERROR",
                    result.get("error", "Detection failed"),
                ),
            )

        return DetectionResponse(
            success=True,
            job_id=result.get("job_id", ""),
            detection_score=result.get("detection_score", 0.5),
            is_spoof=result.get("is_spoof", False),
            confidence=result.get("confidence", 0.0),
            decision=result.get("decision", "UNCERTAIN"),
            quick_mode=True,
            demo_mode=result.get("demo_mode", True),
            duration_seconds=result.get("duration_seconds"),
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            explanation=result.get("explanation"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", "Unexpected error", {"error": str(e)}),
        )


@router.post(
    "/async",
    summary="Start Async Detection",
    description="Start asynchronous detection and return job ID",
)
@limiter.limit("30/minute")
async def detect_async(
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyze"),
    quick_mode: bool = False,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Start asynchronous detection.

    Returns immediately with a job ID. Use `/detect/{job_id}/status` to check progress
    and `/detect/{job_id}/results` to get results when complete.

    **Rate Limit**: 30 requests per minute
    """
    try:
        audio_bytes = await file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Empty audio file"),
            )

        # Preprocess
        import io
        audio_io = io.BytesIO(audio_bytes)
        audio_array, sr = load_and_preprocess_audio(audio_io)

        pipeline = get_pipeline()
        job_id = pipeline.detect_async(audio_array, quick_mode=quick_mode)

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Detection job started. Use /detect/{job_id}/status to check progress.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Async detection start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", str(e)),
        )


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Get Job Status",
    description="Get the status of a detection job",
)
@limiter.limit("100/minute")
async def get_job_status(
    request: Request,
    job_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Get status of a detection job.

    **Rate Limit**: 100 requests per minute
    """
    pipeline = get_pipeline()
    status_result = pipeline.get_job_status(job_id)

    if "error" in status_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("JOB_NOT_FOUND", status_result["error"]),
        )

    return JobStatusResponse(**status_result)


@router.get(
    "/{job_id}/results",
    summary="Get Job Results",
    description="Get the results of a completed detection job",
)
@limiter.limit("100/minute")
async def get_job_results(
    request: Request,
    job_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Get results of a completed detection job.

    Returns full detection results including explanation.

    **Rate Limit**: 100 requests per minute
    """
    pipeline = get_pipeline()
    result = pipeline.get_job_result(job_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("JOB_NOT_FOUND", f"Job {job_id} not found"),
        )

    if "error" in result and result.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_response("JOB_NOT_COMPLETE", result["error"]),
        )

    return convert_numpy_types(result)


@router.get(
    "/demo",
    summary="Demo Detection",
    description="Get demo detection result using synthetic data",
)
@limiter.limit("100/minute")
async def detect_demo(request: Request):
    """
    Get demo detection result.

    Returns a sample detection result using synthetic data.
    Useful for testing integrations and UI development.

    **Rate Limit**: 100 requests per minute
    """
    import numpy as np

    # Generate synthetic audio
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
    audio = audio.astype(np.float32)

    # Run detection
    pipeline = get_pipeline()
    result = pipeline.detect(audio, quick_mode=False)

    return convert_numpy_types(result)
