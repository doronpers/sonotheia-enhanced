"""
Transcription Module

Voice-to-text transcription with provider abstraction,
speaker diarization, and SAR narrative generation support.
"""

from .models import (
    TranscriptSegment,
    Transcript,
    DiarizationSegment,
    DiarizationResult,
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionJobStatus,
    AsyncTranscriptionRequest,
    TranscriptionJobResponse,
    TranscriptionJobStatusResponse,
)
from .transcriber import Transcriber, get_transcriber
from .config import TranscriptionConfig, get_transcription_config

__all__ = [
    # Models
    "TranscriptSegment",
    "Transcript",
    "DiarizationSegment",
    "DiarizationResult",
    "TranscriptionRequest",
    "TranscriptionResponse",
    "TranscriptionJobStatus",
    "AsyncTranscriptionRequest",
    "TranscriptionJobResponse",
    "TranscriptionJobStatusResponse",
    # Transcriber
    "Transcriber",
    "get_transcriber",
    # Config
    "TranscriptionConfig",
    "get_transcription_config",
]
