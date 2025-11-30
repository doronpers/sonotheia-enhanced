"""
Transcription Data Models

Pydantic models for transcription requests, responses, and results.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import re


class TranscriptionJobStatus(str, Enum):
    """Status of a transcription job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TranscriptSegment(BaseModel):
    """Individual segment of a transcript with timing and speaker info."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_time": 0.0,
                "end_time": 2.5,
                "speaker": "SPEAKER_00",
                "text": "Hello, how can I help you today?",
                "confidence": 0.95
            }
        }
    )
    
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    speaker: Optional[str] = Field(None, description="Speaker identifier (from diarization)")
    text: str = Field(..., description="Transcribed text for this segment")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence score (0-1)")
    
    @field_validator('end_time')
    @classmethod
    def end_time_after_start(cls, v, info):
        if 'start_time' in info.data and v < info.data['start_time']:
            raise ValueError('end_time must be >= start_time')
        return v
    
    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('text cannot be empty')
        return v.strip()


class Transcript(BaseModel):
    """Complete transcript of an audio file."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_id": "audio-12345",
                "language": "en",
                "duration": 120.5,
                "segments": [
                    {
                        "start_time": 0.0,
                        "end_time": 2.5,
                        "speaker": "SPEAKER_00",
                        "text": "Hello, how can I help you today?",
                        "confidence": 0.95
                    }
                ],
                "full_text": "Hello, how can I help you today?"
            }
        }
    )
    
    audio_id: str = Field(..., description="Unique identifier for the audio source")
    language: str = Field(default="en", description="Detected or specified language code")
    duration: float = Field(..., ge=0, description="Total audio duration in seconds")
    segments: List[TranscriptSegment] = Field(default_factory=list, description="List of transcript segments")
    full_text: str = Field(default="", description="Complete transcript as single string")
    
    @field_validator('audio_id')
    @classmethod
    def validate_audio_id(cls, v):
        if not v or len(v) > 200:
            raise ValueError('audio_id must be 1-200 characters')
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('audio_id must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if not v or len(v) > 10:
            raise ValueError('language code must be 1-10 characters')
        return v.lower()


class DiarizationSegment(BaseModel):
    """Speaker segment from diarization."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_time": 0.0,
                "end_time": 5.2,
                "speaker": "SPEAKER_00",
                "confidence": 0.92
            }
        }
    )
    
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    speaker: str = Field(..., description="Speaker identifier")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence score")


class DiarizationResult(BaseModel):
    """Result of speaker diarization."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_id": "audio-12345",
                "num_speakers": 2,
                "segments": [
                    {
                        "start_time": 0.0,
                        "end_time": 5.2,
                        "speaker": "SPEAKER_00",
                        "confidence": 0.92
                    }
                ],
                "duration": 120.5
            }
        }
    )
    
    audio_id: str = Field(..., description="Unique identifier for the audio source")
    num_speakers: int = Field(..., ge=0, description="Number of detected speakers")
    segments: List[DiarizationSegment] = Field(default_factory=list, description="Speaker segments")
    duration: float = Field(..., ge=0, description="Total audio duration in seconds")


class TranscriptionRequest(BaseModel):
    """Request model for transcription endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_id": "audio-12345",
                "audio_data_base64": "UklGRi4AAABXQVZFZm10...",
                "language": "en",
                "enable_diarization": False,
                "num_speakers": None,
                "provider": "whisper_local"
            }
        }
    )
    
    audio_id: str = Field(..., description="Unique identifier for this audio", max_length=200)
    audio_data_base64: str = Field(..., description="Base64 encoded audio data")
    language: Optional[str] = Field(None, description="Language code (auto-detect if not provided)")
    enable_diarization: bool = Field(default=False, description="Enable speaker diarization")
    num_speakers: Optional[int] = Field(None, ge=1, le=20, description="Expected number of speakers (for diarization)")
    provider: str = Field(default="whisper_local", description="Transcription provider to use")
    
    @field_validator('audio_id')
    @classmethod
    def validate_audio_id(cls, v):
        if not v or len(v) > 200:
            raise ValueError('audio_id must be 1-200 characters')
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('audio_id must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        valid_providers = ['whisper_local', 'whisper_api', 'assemblyai', 'demo']
        if v not in valid_providers:
            raise ValueError(f'provider must be one of: {", ".join(valid_providers)}')
        return v


class TranscriptionResponse(BaseModel):
    """Response model for transcription endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "transcript": {
                    "audio_id": "audio-12345",
                    "language": "en",
                    "duration": 120.5,
                    "segments": [],
                    "full_text": "Hello, how can I help you today?"
                },
                "diarization": None,
                "processing_time_seconds": 15.2,
                "provider": "whisper_local"
            }
        }
    )
    
    success: bool = Field(..., description="Whether transcription succeeded")
    transcript: Optional[Transcript] = Field(None, description="Transcript result")
    diarization: Optional[DiarizationResult] = Field(None, description="Diarization result (if enabled)")
    processing_time_seconds: float = Field(..., ge=0, description="Total processing time")
    provider: str = Field(..., description="Provider used for transcription")
    error: Optional[str] = Field(None, description="Error message if failed")


class AsyncTranscriptionRequest(BaseModel):
    """Request model for async transcription endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_id": "audio-12345",
                "audio_data_base64": "UklGRi4AAABXQVZFZm10...",
                "language": "en",
                "enable_diarization": True,
                "num_speakers": 2,
                "provider": "whisper_local",
                "priority": "normal",
                "callback_url": None
            }
        }
    )
    
    audio_id: str = Field(..., description="Unique identifier for this audio", max_length=200)
    audio_data_base64: str = Field(..., description="Base64 encoded audio data")
    language: Optional[str] = Field(None, description="Language code (auto-detect if not provided)")
    enable_diarization: bool = Field(default=False, description="Enable speaker diarization")
    num_speakers: Optional[int] = Field(None, ge=1, le=20, description="Expected number of speakers")
    provider: str = Field(default="whisper_local", description="Transcription provider to use")
    priority: str = Field(default="normal", description="Job priority: high, normal, low")
    callback_url: Optional[str] = Field(None, description="URL to POST results when complete")
    
    @field_validator('audio_id')
    @classmethod
    def validate_audio_id(cls, v):
        if not v or len(v) > 200:
            raise ValueError('audio_id must be 1-200 characters')
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('audio_id must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        valid_providers = ['whisper_local', 'whisper_api', 'assemblyai', 'demo']
        if v not in valid_providers:
            raise ValueError(f'provider must be one of: {", ".join(valid_providers)}')
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        valid_priorities = ['high', 'normal', 'low']
        if v not in valid_priorities:
            raise ValueError(f'priority must be one of: {", ".join(valid_priorities)}')
        return v


class TranscriptionJobResponse(BaseModel):
    """Response model for async transcription job submission."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "txn-job-12345",
                "audio_id": "audio-12345",
                "status": "pending",
                "message": "Transcription job submitted successfully",
                "submitted_at": "2024-01-15T10:30:00Z",
                "endpoints": {
                    "status": "/api/transcribe/txn-job-12345",
                    "result": "/api/transcribe/txn-job-12345/result"
                }
            }
        }
    )
    
    job_id: str = Field(..., description="Unique job identifier")
    audio_id: str = Field(..., description="Audio identifier from request")
    status: TranscriptionJobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    submitted_at: datetime = Field(default_factory=datetime.now, description="Submission timestamp")
    endpoints: dict = Field(default_factory=dict, description="Endpoints for checking job status")


class TranscriptionJobStatusResponse(BaseModel):
    """Response model for transcription job status check."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "txn-job-12345",
                "audio_id": "audio-12345",
                "status": "processing",
                "progress": 0.45,
                "message": "Transcribing audio...",
                "started_at": "2024-01-15T10:30:05Z",
                "estimated_time_remaining": 30.0
            }
        }
    )
    
    job_id: str = Field(..., description="Job identifier")
    audio_id: str = Field(..., description="Audio identifier")
    status: TranscriptionJobStatus = Field(..., description="Current job status")
    progress: Optional[float] = Field(None, ge=0, le=1, description="Progress (0-1)")
    message: Optional[str] = Field(None, description="Status message")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    estimated_time_remaining: Optional[float] = Field(None, ge=0, description="Estimated seconds remaining")
