"""
Transcription API Router

REST API endpoints for transcription services.
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import Optional
import base64
import threading

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException, Request, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field

from api.middleware import limiter, verify_api_key, get_error_response
from core.module_registry import is_module_enabled
from transcription import (
    get_transcriber,
    get_transcription_config,
    TranscriptionRequest,
    TranscriptionResponse,
    AsyncTranscriptionRequest,
    TranscriptionJobResponse,
    TranscriptionJobStatusResponse,
    TranscriptionJobStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["transcription"])

# In-memory job storage for demo (use database/Redis in production)
_jobs = {}
_jobs_lock = threading.RLock()  # Thread-safe access to _jobs dictionary


def check_module_enabled():
    """Check if transcription module is enabled."""
    if not is_module_enabled("transcription"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_error_response(
                "MODULE_DISABLED",
                "Transcription module is disabled"
            )
        )


class TranscriptionHealthResponse(BaseModel):
    """Health check response for transcription module."""
    enabled: bool = Field(..., description="Whether transcription is enabled")
    demo_mode: bool = Field(..., description="Whether running in demo mode")
    available_providers: list = Field(..., description="List of available providers")
    providers: dict = Field(..., description="Status of each provider")


class DiarizeRequest(BaseModel):
    """Request model for diarization-only endpoint."""
    audio_id: str = Field(..., description="Unique audio identifier", max_length=200)
    audio_data_base64: str = Field(..., description="Base64 encoded audio data")
    num_speakers: Optional[int] = Field(None, ge=1, le=20, description="Expected number of speakers")


@router.get(
    "/transcribe/health",
    response_model=TranscriptionHealthResponse,
    summary="Transcription Health Check",
    description="Check health status of transcription services",
    response_description="Health status of transcription providers"
)
@limiter.limit("60/minute")
async def transcription_health(request: Request):
    """
    Check health of transcription services.
    
    Returns availability status for each transcription provider.
    """
    check_module_enabled()
    
    try:
        transcriber = get_transcriber()
        health = await transcriber.check_health()
        
        return TranscriptionHealthResponse(
            enabled=health["enabled"],
            demo_mode=health["demo_mode"],
            available_providers=health["available_providers"],
            providers=health["providers"]
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("HEALTH_CHECK_ERROR", str(e))
        )


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe Audio",
    description="Transcribe audio file to text with optional speaker diarization",
    response_description="Transcription result with segments"
)
@limiter.limit("30/minute")
async def transcribe_audio(
    request: Request,
    transcription_request: TranscriptionRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Transcribe audio to text.
    
    Supports multiple providers:
    - `whisper_local`: Local Whisper model (privacy-sensitive)
    - `whisper_api`: OpenAI Whisper API (requires API key)
    - `assemblyai`: AssemblyAI API (requires API key)
    - `demo`: Demo provider for testing
    
    **Rate Limit**: 30 requests per minute
    
    **Audio Formats**: WAV, MP3, FLAC, OGG
    
    **Max Size**: 800 MB (use async endpoint for large files)
    """
    check_module_enabled()
    
    try:
        # Basic validation
        config = get_transcription_config()
        
        # Check audio size
        try:
            audio_bytes = base64.b64decode(transcription_request.audio_data_base64)
            if len(audio_bytes) > config.max_audio_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=get_error_response(
                        "PAYLOAD_TOO_LARGE",
                        f"Audio data exceeds maximum size of {config.max_audio_size_mb}MB"
                    )
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_error_response("INVALID_AUDIO", "Invalid base64 audio data")
            )
        
        # Get transcriber
        transcriber = get_transcriber()
        
        # Perform transcription
        result = await transcriber.transcribe(
            audio_data_base64=transcription_request.audio_data_base64,
            audio_id=transcription_request.audio_id,
            language=transcription_request.language,
            provider=transcription_request.provider,
            enable_diarization=transcription_request.enable_diarization,
            num_speakers=transcription_request.num_speakers
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_error_response("TRANSCRIPTION_ERROR", result.error)
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", f"Transcription failed: {str(e)}")
        )


@router.post(
    "/transcribe/async",
    response_model=TranscriptionJobResponse,
    summary="Submit Async Transcription Job",
    description="Submit audio for asynchronous transcription (for large files or batch processing)",
    response_description="Job submission confirmation"
)
@limiter.limit("20/minute")
async def submit_async_transcription(
    request: Request,
    transcription_request: AsyncTranscriptionRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Submit audio for async transcription.
    
    Returns immediately with a job_id. Use the status and result endpoints
    to check progress and retrieve results.
    
    **Use Cases:**
    - Large audio files (> 100 MB)
    - Batch processing
    - Long-running transcriptions
    
    **Rate Limit**: 20 requests per minute
    """
    check_module_enabled()
    
    try:
        config = get_transcription_config()
        
        # Validate audio size
        try:
            audio_bytes = base64.b64decode(transcription_request.audio_data_base64)
            if len(audio_bytes) > config.max_audio_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=get_error_response(
                        "PAYLOAD_TOO_LARGE",
                        f"Audio data exceeds maximum size of {config.max_audio_size_mb}MB"
                    )
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_error_response("INVALID_AUDIO", "Invalid base64 audio data")
            )
        
        # Generate job ID
        import uuid
        job_id = f"txn-{uuid.uuid4().hex[:12]}"
        
        # Store job info
        _jobs[job_id] = {
            "audio_id": transcription_request.audio_id,
            "status": TranscriptionJobStatus.PENDING,
            "progress": 0.0,
            "message": "Job queued",
            "submitted_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        # Try to use Celery if available, otherwise use background task
        try:
            from tasks.transcription_tasks import transcribe_async_task
            
            # Submit to Celery
            priority_map = {"high": 3, "normal": 5, "low": 7}
            task_priority = priority_map.get(transcription_request.priority, 5)
            
            task = transcribe_async_task.apply_async(
                kwargs={
                    "job_id": job_id,
                    "audio_data_base64": transcription_request.audio_data_base64,
                    "audio_id": transcription_request.audio_id,
                    "language": transcription_request.language,
                    "provider": transcription_request.provider,
                    "enable_diarization": transcription_request.enable_diarization,
                    "num_speakers": transcription_request.num_speakers,
                    "callback_url": transcription_request.callback_url
                },
                priority=task_priority
            )
            
            # Update job with Celery task ID
            _jobs[job_id]["celery_task_id"] = task.id
            
        except ImportError:
            # Celery not available, use FastAPI background task
            logger.info("Celery not available, using background task")
            background_tasks.add_task(
                _run_transcription_background,
                job_id=job_id,
                audio_data_base64=transcription_request.audio_data_base64,
                audio_id=transcription_request.audio_id,
                language=transcription_request.language,
                provider=transcription_request.provider,
                enable_diarization=transcription_request.enable_diarization,
                num_speakers=transcription_request.num_speakers
            )
        
        logger.info(f"Async transcription job submitted: {job_id}")
        
        return TranscriptionJobResponse(
            job_id=job_id,
            audio_id=transcription_request.audio_id,
            status=TranscriptionJobStatus.PENDING,
            message="Transcription job submitted successfully",
            submitted_at=_jobs[job_id]["submitted_at"],
            endpoints={
                "status": f"/api/transcribe/{job_id}",
                "result": f"/api/transcribe/{job_id}/result"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit async transcription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("SUBMISSION_ERROR", f"Failed to submit job: {str(e)}")
        )


async def _run_transcription_background(
    job_id: str,
    audio_data_base64: str,
    audio_id: str,
    language: Optional[str],
    provider: str,
    enable_diarization: bool,
    num_speakers: Optional[int]
):
    """Background task for transcription."""
    try:
        _jobs[job_id]["status"] = TranscriptionJobStatus.PROCESSING
        _jobs[job_id]["started_at"] = datetime.now()
        _jobs[job_id]["message"] = "Processing transcription"
        _jobs[job_id]["progress"] = 0.1
        
        transcriber = get_transcriber()
        
        result = await transcriber.transcribe(
            audio_data_base64=audio_data_base64,
            audio_id=audio_id,
            language=language,
            provider=provider,
            enable_diarization=enable_diarization,
            num_speakers=num_speakers
        )
        
        _jobs[job_id]["completed_at"] = datetime.now()
        
        if result.success:
            _jobs[job_id]["status"] = TranscriptionJobStatus.COMPLETED
            _jobs[job_id]["progress"] = 1.0
            _jobs[job_id]["message"] = "Transcription completed"
            _jobs[job_id]["result"] = result
        else:
            _jobs[job_id]["status"] = TranscriptionJobStatus.FAILED
            _jobs[job_id]["message"] = result.error
            _jobs[job_id]["error"] = result.error
            
    except Exception as e:
        logger.error(f"Background transcription failed for {job_id}: {e}")
        _jobs[job_id]["status"] = TranscriptionJobStatus.FAILED
        _jobs[job_id]["completed_at"] = datetime.now()
        _jobs[job_id]["message"] = str(e)
        _jobs[job_id]["error"] = str(e)


@router.get(
    "/transcribe/config",
    summary="Get Transcription Config",
    description="Get current transcription configuration",
    response_description="Transcription configuration"
)
@limiter.limit("60/minute")
async def get_config(request: Request):
    """Get current transcription configuration (safe subset)."""
    check_module_enabled()
    
    config = get_transcription_config()
    return config.to_dict()


@router.get(
    "/transcribe/{job_id}",
    response_model=TranscriptionJobStatusResponse,
    summary="Get Transcription Job Status",
    description="Check status of an async transcription job",
    response_description="Current job status"
)
@limiter.limit("100/minute")
async def get_transcription_status(
    request: Request,
    job_id: str,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Get status of an async transcription job.
    
    **Status Values:**
    - `pending`: Job is queued
    - `processing`: Job is being processed
    - `completed`: Job completed successfully
    - `failed`: Job failed
    - `cancelled`: Job was cancelled
    """
    check_module_enabled()
    
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("JOB_NOT_FOUND", f"Job {job_id} not found")
        )
    
    job = _jobs[job_id]
    
    return TranscriptionJobStatusResponse(
        job_id=job_id,
        audio_id=job["audio_id"],
        status=job["status"],
        progress=job.get("progress"),
        message=job.get("message"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at")
    )


@router.get(
    "/transcribe/{job_id}/result",
    response_model=TranscriptionResponse,
    summary="Get Transcription Job Result",
    description="Get result of a completed transcription job",
    response_description="Transcription result"
)
@limiter.limit("100/minute")
async def get_transcription_result(
    request: Request,
    job_id: str,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Get result of a completed transcription job.
    
    Returns the transcription result if the job completed successfully.
    Returns an error if the job is still processing or failed.
    """
    check_module_enabled()
    
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("JOB_NOT_FOUND", f"Job {job_id} not found")
        )
    
    job = _jobs[job_id]
    
    if job["status"] == TranscriptionJobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_error_response("JOB_PENDING", "Job has not started yet")
        )
    
    if job["status"] == TranscriptionJobStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_error_response("JOB_PROCESSING", "Job is still processing")
        )
    
    if job["status"] == TranscriptionJobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=get_error_response("JOB_FAILED", job.get("error", "Job failed"))
        )
    
    if job["status"] == TranscriptionJobStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=get_error_response("JOB_CANCELLED", "Job was cancelled")
        )
    
    result = job.get("result")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("RESULT_MISSING", "Job completed but result is missing")
        )
    
    return result


@router.post(
    "/diarize",
    summary="Speaker Diarization",
    description="Perform speaker diarization on audio (identifies different speakers)",
    response_description="Diarization result with speaker segments"
)
@limiter.limit("20/minute")
async def diarize_audio(
    request: Request,
    diarize_request: DiarizeRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Perform speaker diarization on audio.
    
    Identifies different speakers and their speaking segments.
    
    **Rate Limit**: 20 requests per minute
    """
    check_module_enabled()
    
    try:
        from transcription.diarization import SpeakerDiarizer
        import numpy as np
        
        config = get_transcription_config()
        
        # Decode audio
        try:
            audio_bytes = base64.b64decode(diarize_request.audio_data_base64)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_error_response("INVALID_AUDIO", "Invalid base64 audio data")
            )
        
        # Load audio
        transcriber = get_transcriber()
        audio_data, sample_rate = await transcriber._load_audio(diarize_request.audio_data_base64)
        
        # Perform diarization
        diarizer = SpeakerDiarizer(config)
        result = await diarizer.diarize(
            audio_data=audio_data,
            sample_rate=sample_rate,
            audio_id=diarize_request.audio_id,
            num_speakers=diarize_request.num_speakers
        )
        
        return {
            "success": True,
            "audio_id": result.audio_id,
            "num_speakers": result.num_speakers,
            "duration": result.duration,
            "segments": [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "speaker": seg.speaker,
                    "confidence": seg.confidence
                }
                for seg in result.segments
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diarization failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("DIARIZATION_ERROR", f"Diarization failed: {str(e)}")
        )
