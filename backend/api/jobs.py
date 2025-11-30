"""
Jobs API Router
Endpoints for async job management: submission, status, results, and cancellation.
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException, Request, Depends, status  # noqa: E402
from pydantic import BaseModel, Field, ConfigDict  # noqa: E402
import base64  # noqa: E402

from api.middleware import limiter, verify_api_key, get_error_response  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["jobs"])


# Request/Response Models
class AsyncAnalysisRequest(BaseModel):
    """Request model for async analysis submission."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_data_base64": "UklGRi4AAABXQVZFZm10...",
                "call_id": "CALL-2024-001",
                "customer_id": "CUST-12345",
                "transaction_id": "TXN-001",
                "amount_usd": 50000.00,
                "destination_country": "US",
                "channel": "phone",
                "codec": "landline",
                "priority": "normal",
            }
        }
    )

    audio_data_base64: str = Field(..., description="Base64 encoded audio data")
    call_id: str = Field(..., description="Unique call identifier", max_length=100)
    customer_id: str = Field(..., description="Customer identifier", max_length=100)
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID", max_length=100)
    amount_usd: Optional[float] = Field(None, description="Transaction amount in USD", gt=0)
    destination_country: Optional[str] = Field(None, description="Destination country (2-letter code)", max_length=2)
    channel: str = Field(default="phone", description="Call channel (phone, voip, etc.)")
    codec: str = Field(default="landline", description="Codec to simulate: landline, mobile, voip, clean")
    priority: str = Field(default="normal", description="Task priority: high, normal, low")


class JobSubmissionResponse(BaseModel):
    """Response model for job submission."""

    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")
    submitted_at: str = Field(..., description="Job submission timestamp")
    priority: str = Field(..., description="Task priority")
    endpoints: Dict[str, str] = Field(..., description="Endpoints for checking status and getting results")


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current job status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    started_at: Optional[str] = Field(None, description="When job started")
    completed_at: Optional[str] = Field(None, description="When job completed")
    estimated_time_remaining: Optional[float] = Field(None, description="Estimated remaining time in seconds")


class JobResultResponse(BaseModel):
    """Response model for job result."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Final job status")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")


class JobCancellationResponse(BaseModel):
    """Response model for job cancellation."""

    job_id: str = Field(..., description="Job identifier")
    cancelled: bool = Field(..., description="Whether cancellation succeeded")
    message: str = Field(..., description="Cancellation message")
    previous_status: str = Field(..., description="Job status before cancellation")


def _get_celery_app():
    """Get Celery app instance."""
    try:
        from celery_app import app as celery_app

        return celery_app
    except ImportError as e:
        logger.error(f"Failed to import Celery app: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
        )


def _get_task_status(task_result) -> dict:
    """Extract status information from Celery task result."""
    status_info = {
        "status": task_result.status,
        "job_id": task_result.id,
    }

    if task_result.status == "PENDING":
        status_info["message"] = "Job is queued and waiting to be processed"
    elif task_result.status == "STARTED":
        status_info["message"] = "Job has started processing"
    elif task_result.status == "PROCESSING":
        # Custom state with progress info
        info = task_result.info or {}
        status_info["progress"] = info.get("progress", 0)
        status_info["message"] = info.get("message", "Processing")
    elif task_result.status == "SUCCESS":
        status_info["message"] = "Job completed successfully"
        status_info["result"] = task_result.result
    elif task_result.status == "FAILURE":
        status_info["message"] = "Job failed"
        status_info["error"] = str(task_result.result) if task_result.result else "Unknown error"
    elif task_result.status == "REVOKED":
        status_info["message"] = "Job was cancelled"
    else:
        status_info["message"] = f"Job status: {task_result.status}"

    return status_info


@router.post(
    "/analyze/async",
    response_model=JobSubmissionResponse,
    summary="Submit Async Analysis Job",
    description="Submit an audio call for asynchronous analysis. Returns a job_id for tracking.",
    response_description="Job submission confirmation with tracking ID",
)
@limiter.limit("50/minute")
async def submit_async_analysis(
    request: Request, analysis_request: AsyncAnalysisRequest, api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Submit audio call for async analysis.

    This endpoint queues the analysis job and returns immediately with a job_id.
    Use the returned endpoints to check status and retrieve results.

    **Task Pipeline:**
    1. Audio loading and codec simulation
    2. Feature extraction (LFCC, log-spectrogram)
    3. Deepfake/spoof detection
    4. Risk factor analysis
    5. SAR generation (if high risk)

    **Rate Limit**: 50 requests per minute
    """
    try:
        # Import task
        from tasks.analysis_tasks import analyze_call_async

        # Validate audio data size (basic check)
        try:
            audio_bytes = base64.b64decode(analysis_request.audio_data_base64)
            if len(audio_bytes) > 15 * 1024 * 1024:  # 15MB limit
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=get_error_response("PAYLOAD_TOO_LARGE", "Audio data exceeds maximum size of 15MB"),
                )
        except base64.binascii.Error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=get_error_response("INVALID_AUDIO_DATA", "Audio data is not valid base64"),
            )

        # Map priority to Celery priority
        priority_map = {"high": 3, "normal": 5, "low": 7}
        task_priority = priority_map.get(analysis_request.priority, 5)

        # Submit task
        task = analyze_call_async.apply_async(
            kwargs={
                "audio_data_base64": analysis_request.audio_data_base64,
                "call_id": analysis_request.call_id,
                "customer_id": analysis_request.customer_id,
                "transaction_id": analysis_request.transaction_id,
                "amount_usd": analysis_request.amount_usd,
                "destination_country": analysis_request.destination_country,
                "channel": analysis_request.channel,
                "codec": analysis_request.codec,
            },
            priority=task_priority,
        )

        job_id = task.id
        submitted_at = datetime.now().isoformat()

        logger.info(f"Submitted async analysis job: {job_id} for call {analysis_request.call_id}")

        return JobSubmissionResponse(
            job_id=job_id,
            status="PENDING",
            message="Job submitted successfully and queued for processing",
            submitted_at=submitted_at,
            priority=analysis_request.priority,
            endpoints={
                "status": f"/api/jobs/{job_id}",
                "result": f"/api/jobs/{job_id}/result",
                "cancel": f"/api/jobs/{job_id}",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit async analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("SUBMISSION_ERROR", f"Failed to submit analysis job: {str(e)}"),
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status",
    description="Get the current status of an async job",
    response_description="Job status information",
)
@limiter.limit("100/minute")
async def get_job_status(request: Request, job_id: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get the status of an async job.

    **Status Values:**
    - `PENDING`: Job is queued
    - `STARTED`: Job has started
    - `PROCESSING`: Job is processing (includes progress %)
    - `SUCCESS`: Job completed successfully
    - `FAILURE`: Job failed
    - `REVOKED`: Job was cancelled

    **Rate Limit**: 100 requests per minute
    """
    try:
        celery_app = _get_celery_app()
        task_result = celery_app.AsyncResult(job_id)

        status_info = _get_task_status(task_result)

        response = JobStatusResponse(
            job_id=job_id,
            status=status_info["status"],
            progress=status_info.get("progress"),
            message=status_info.get("message"),
        )

        return response

    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Redis connection failed for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
        )
    except Exception as e:
        # Check for connection-related errors
        error_str = str(e).lower()
        if "connection" in error_str or "redis" in error_str or "refused" in error_str:
            logger.error(f"Redis connection failed for job {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
            )
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("STATUS_ERROR", f"Failed to get job status: {str(e)}"),
        )


@router.get(
    "/jobs/{job_id}/result",
    response_model=JobResultResponse,
    summary="Get Job Result",
    description="Get the result of a completed async job",
    response_description="Job result data",
)
@limiter.limit("100/minute")
async def get_job_result(request: Request, job_id: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get the result of a completed job.

    Returns the full analysis result if the job completed successfully.
    Returns an error message if the job failed.

    **Note**: Results are available for 1 hour after completion.

    **Rate Limit**: 100 requests per minute
    """
    try:
        celery_app = _get_celery_app()
        task_result = celery_app.AsyncResult(job_id)

        if task_result.status == "PENDING":
            return JobResultResponse(job_id=job_id, status="PENDING", result=None, error="Job has not completed yet")

        if task_result.status in ["STARTED", "PROCESSING"]:
            info = task_result.info or {}
            return JobResultResponse(
                job_id=job_id,
                status=task_result.status,
                result=None,
                error=f"Job is still processing ({info.get('progress', 0):.0f}% complete)",
            )

        if task_result.status == "SUCCESS":
            result_data = task_result.result
            processing_time = None

            if isinstance(result_data, dict):
                data = result_data.get("data", {})
                processing_time = data.get("processing_time_seconds")

            return JobResultResponse(
                job_id=job_id,
                status="COMPLETED",
                result=result_data,
                completed_at=datetime.now().isoformat(),
                processing_time_seconds=processing_time,
            )

        if task_result.status == "FAILURE":
            return JobResultResponse(
                job_id=job_id,
                status="FAILED",
                result=None,
                error=str(task_result.result) if task_result.result else "Unknown error",
            )

        if task_result.status == "REVOKED":
            return JobResultResponse(job_id=job_id, status="CANCELLED", result=None, error="Job was cancelled")

        return JobResultResponse(
            job_id=job_id, status=task_result.status, result=None, error=f"Unexpected status: {task_result.status}"
        )

    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Redis connection failed for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
        )
    except Exception as e:
        # Check for connection-related errors
        error_str = str(e).lower()
        if "connection" in error_str or "redis" in error_str or "refused" in error_str:
            logger.error(f"Redis connection failed for job {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
            )
        logger.error(f"Failed to get job result for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("RESULT_ERROR", f"Failed to get job result: {str(e)}"),
        )


@router.delete(
    "/jobs/{job_id}",
    response_model=JobCancellationResponse,
    summary="Cancel Job",
    description="Cancel a pending or running async job",
    response_description="Job cancellation result",
)
@limiter.limit("50/minute")
async def cancel_job(request: Request, job_id: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Cancel an async job.

    **Note**: Only PENDING and STARTED jobs can be cancelled.
    Already completed or failed jobs cannot be cancelled.

    **Rate Limit**: 50 requests per minute
    """
    try:
        celery_app = _get_celery_app()
        task_result = celery_app.AsyncResult(job_id)

        previous_status = task_result.status

        # Check if job can be cancelled
        if previous_status in ["SUCCESS", "FAILURE", "REVOKED"]:
            return JobCancellationResponse(
                job_id=job_id,
                cancelled=False,
                message=f"Job cannot be cancelled (status: {previous_status})",
                previous_status=previous_status,
            )

        # Revoke the task
        task_result.revoke(terminate=True)

        logger.info(f"Cancelled job: {job_id} (previous status: {previous_status})")

        return JobCancellationResponse(
            job_id=job_id, cancelled=True, message="Job cancellation requested", previous_status=previous_status
        )

    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Redis connection failed for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
        )
    except Exception as e:
        # Check for connection-related errors
        error_str = str(e).lower()
        if "connection" in error_str or "redis" in error_str or "refused" in error_str:
            logger.error(f"Redis connection failed for job {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=get_error_response("SERVICE_UNAVAILABLE", "Task queue service is not available"),
            )
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("CANCELLATION_ERROR", f"Failed to cancel job: {str(e)}"),
        )


@router.get(
    "/jobs",
    summary="List Jobs",
    description="List recent jobs (limited functionality without database)",
    response_description="List of recent job IDs",
)
@limiter.limit("50/minute")
async def list_jobs(
    request: Request,
    status_filter: Optional[str] = None,
    limit: int = 10,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    List recent jobs.

    **Note**: This endpoint has limited functionality without a persistent
    job database. Consider implementing a database backend for full job
    listing capabilities.

    **Rate Limit**: 50 requests per minute
    """
    # Without a database, we can't list jobs
    # This is a placeholder that could be enhanced with Redis inspection
    # or a proper job database
    return {
        "message": "Job listing requires job IDs. Use the job_id returned from /api/analyze/async",
        "endpoints": {
            "submit": "POST /api/analyze/async",
            "status": "GET /api/jobs/{job_id}",
            "result": "GET /api/jobs/{job_id}/result",
            "cancel": "DELETE /api/jobs/{job_id}",
        },
        "note": "Store job_ids from submission responses to track your jobs",
    }
