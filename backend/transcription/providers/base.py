"""
Base Transcription Provider

Abstract base class for all transcription providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import numpy as np
import logging

from ..models import Transcript, TranscriptSegment

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    
    def __init__(self, message: str, provider: str = None, recoverable: bool = False):
        self.message = message
        self.provider = provider
        self.recoverable = recoverable
        super().__init__(message)


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""
    
    def __init__(self, config):
        """
        Initialize the provider.
        
        Args:
            config: TranscriptionConfig instance
        """
        self.config = config
        self._healthy = True
        self._consecutive_failures = 0
        self.name = "base"
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None,
        **kwargs
    ) -> Transcript:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            language: Optional language code (auto-detect if None)
            **kwargs: Additional provider-specific options
        
        Returns:
            Transcript object with segments and full text
        
        Raises:
            TranscriptionError: If transcription fails
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider is available and healthy.
        
        Returns:
            True if provider is ready to handle requests
        """
        pass
    
    @property
    def healthy(self) -> bool:
        """Check if provider is healthy."""
        return self._healthy
    
    def mark_failure(self) -> None:
        """Mark a failure for health tracking."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.config.max_consecutive_failures:
            if self.config.auto_disable_on_failure:
                logger.warning(f"Provider {self.name} disabled after {self._consecutive_failures} failures")
                self._healthy = False
    
    def mark_success(self) -> None:
        """Mark a success for health tracking."""
        self._consecutive_failures = 0
        self._healthy = True
    
    def _convert_numpy_to_native(self, value):
        """
        Convert numpy types to native Python types for JSON serialization.
        
        Args:
            value: Any value that might contain numpy types
        
        Returns:
            Value with numpy types converted to native Python types
        """
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, dict):
            return {k: self._convert_numpy_to_native(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._convert_numpy_to_native(v) for v in value]
        return value
    
    def _create_transcript(
        self,
        audio_id: str,
        segments: List[dict],
        language: str,
        duration: float
    ) -> Transcript:
        """
        Helper to create a Transcript from segment data.
        
        Args:
            audio_id: Audio identifier
            segments: List of segment dictionaries
            language: Detected/specified language
            duration: Total audio duration
        
        Returns:
            Transcript object
        """
        transcript_segments = []
        full_text_parts = []
        
        for seg in segments:
            # Convert numpy types
            start_time = self._convert_numpy_to_native(seg.get('start', 0))
            end_time = self._convert_numpy_to_native(seg.get('end', 0))
            text = seg.get('text', '').strip()
            confidence = self._convert_numpy_to_native(seg.get('confidence', 1.0))
            speaker = seg.get('speaker')
            
            if text:
                transcript_segments.append(TranscriptSegment(
                    start_time=float(start_time),
                    end_time=float(end_time),
                    text=text,
                    confidence=float(confidence),
                    speaker=speaker
                ))
                full_text_parts.append(text)
        
        full_text = ' '.join(full_text_parts)
        
        return Transcript(
            audio_id=audio_id,
            language=language,
            duration=float(self._convert_numpy_to_native(duration)),
            segments=transcript_segments,
            full_text=full_text
        )
