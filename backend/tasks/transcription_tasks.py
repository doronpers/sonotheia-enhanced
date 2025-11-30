"""
Transcription Celery Tasks

Async tasks for transcription processing via Celery.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Celery
try:
    from celery_app import app as celery_app
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None
    logger.warning("Celery not available, transcription tasks will run synchronously")


def _make_task(func):
    """Decorator to create Celery task if available, otherwise return function."""
    if CELERY_AVAILABLE and celery_app:
        return celery_app.task(bind=True, name=func.__name__)(func)
    return func


@_make_task
def transcribe_async_task(
    self,
    job_id: str,
    audio_data_base64: str,
    audio_id: str,
    language: Optional[str] = None,
    provider: str = "whisper_local",
    enable_diarization: bool = False,
    num_speakers: Optional[int] = None,
    callback_url: Optional[str] = None
):
    """
    Async transcription task.
    
    Args:
        job_id: Unique job identifier
        audio_data_base64: Base64 encoded audio data
        audio_id: Audio identifier
        language: Language code (auto-detect if None)
        provider: Transcription provider
        enable_diarization: Enable speaker diarization
        num_speakers: Expected number of speakers
        callback_url: URL to POST results when complete
    
    Returns:
        Dict with transcription result
    """
    import asyncio
    
    try:
        # Update progress if Celery task
        if hasattr(self, 'update_state'):
            self.update_state(
                state='PROCESSING',
                meta={'progress': 0.1, 'message': 'Starting transcription'}
            )
        
        logger.info(f"Starting transcription task for job {job_id}")
        
        # Import here to avoid circular imports
        from transcription import get_transcriber
        
        transcriber = get_transcriber()
        
        # Run the async transcription
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if hasattr(self, 'update_state'):
                self.update_state(
                    state='PROCESSING',
                    meta={'progress': 0.3, 'message': 'Loading audio'}
                )
            
            result = loop.run_until_complete(
                transcriber.transcribe(
                    audio_data_base64=audio_data_base64,
                    audio_id=audio_id,
                    language=language,
                    provider=provider,
                    enable_diarization=enable_diarization,
                    num_speakers=num_speakers
                )
            )
        finally:
            asyncio.set_event_loop(None)
            loop.close()
        
        if hasattr(self, 'update_state'):
            self.update_state(
                state='PROCESSING',
                meta={'progress': 0.9, 'message': 'Finalizing result'}
            )
        
        # Prepare result
        result_data = {
            "job_id": job_id,
            "success": result.success,
            "processing_time_seconds": result.processing_time_seconds,
            "provider": result.provider,
            "completed_at": datetime.now().isoformat()
        }
        
        if result.success:
            result_data["transcript"] = {
                "audio_id": result.transcript.audio_id,
                "language": result.transcript.language,
                "duration": result.transcript.duration,
                "full_text": result.transcript.full_text,
                "segments": [
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                        "confidence": seg.confidence,
                        "speaker": seg.speaker
                    }
                    for seg in result.transcript.segments
                ]
            }
            
            if result.diarization:
                result_data["diarization"] = {
                    "audio_id": result.diarization.audio_id,
                    "num_speakers": result.diarization.num_speakers,
                    "duration": result.diarization.duration,
                    "segments": [
                        {
                            "start_time": seg.start_time,
                            "end_time": seg.end_time,
                            "speaker": seg.speaker,
                            "confidence": seg.confidence
                        }
                        for seg in result.diarization.segments
                    ]
                }
        else:
            result_data["error"] = result.error
        
        # Send callback if configured
        if callback_url and result.success:
            _send_callback(callback_url, result_data)
        
        logger.info(f"Transcription task completed for job {job_id}: success={result.success}")
        
        return result_data
        
    except Exception as e:
        logger.error(f"Transcription task failed for job {job_id}: {str(e)}", exc_info=True)
        
        error_result = {
            "job_id": job_id,
            "success": False,
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        
        # Send error callback
        if callback_url:
            _send_callback(callback_url, error_result)
        
        raise


def _send_callback(callback_url: str, data: dict):
    """Send result to callback URL."""
    try:
        import requests
        
        response = requests.post(
            callback_url,
            json=data,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code >= 400:
            logger.warning(f"Callback to {callback_url} returned status {response.status_code}")
        else:
            logger.info(f"Callback sent to {callback_url}")
            
    except Exception as e:
        logger.error(f"Failed to send callback to {callback_url}: {e}")
