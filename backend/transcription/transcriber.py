"""
Main Transcriber Interface

High-level transcription interface that combines providers and diarization.
Handles audio loading, chunking, and provider abstraction.
"""

import base64
import io
import logging
import os
import tempfile
import time
from typing import Optional, Tuple
import numpy as np

from .config import TranscriptionConfig, get_transcription_config
from .models import (
    Transcript,
    TranscriptionResponse,
    DiarizationResult
)
from .providers import get_provider, TranscriptionError
from .diarization import SpeakerDiarizer

logger = logging.getLogger(__name__)

# Singleton transcriber instance
_transcriber: Optional["Transcriber"] = None


class Transcriber:
    """
    High-level transcription interface.
    
    Handles:
    - Audio loading from various formats
    - Provider selection and fallback
    - Optional speaker diarization
    - Large file chunking/streaming
    """
    
    def __init__(self, config: Optional[TranscriptionConfig] = None):
        """
        Initialize transcriber.
        
        Args:
            config: TranscriptionConfig instance (uses default if None)
        """
        self.config = config or get_transcription_config()
        self._diarizer = SpeakerDiarizer(self.config)
        self._providers = {}
        
        logger.info(f"Transcriber initialized with config: {self.config.to_dict()}")
    
    async def transcribe(
        self,
        audio_data_base64: str,
        audio_id: str,
        language: Optional[str] = None,
        provider: Optional[str] = None,
        enable_diarization: bool = False,
        num_speakers: Optional[int] = None
    ) -> TranscriptionResponse:
        """
        Transcribe audio from base64-encoded data.
        
        Args:
            audio_data_base64: Base64 encoded audio data
            audio_id: Unique identifier for the audio
            language: Language code (auto-detect if None)
            provider: Provider to use (uses default if None)
            enable_diarization: Whether to perform speaker diarization
            num_speakers: Expected number of speakers (for diarization)
        
        Returns:
            TranscriptionResponse with transcript and optional diarization
        """
        start_time = time.time()
        provider_name = provider or self.config.default_provider
        
        try:
            # Decode and load audio
            audio_data, sample_rate = await self._load_audio(audio_data_base64)
            
            # Get provider
            transcription_provider = self._get_provider(provider_name)
            
            # Perform transcription
            transcript = await transcription_provider.transcribe(
                audio_data=audio_data,
                sample_rate=sample_rate,
                language=language,
                audio_id=audio_id
            )
            
            # Perform diarization if enabled
            diarization = None
            if enable_diarization:
                diarization = await self._diarizer.diarize(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    audio_id=audio_id,
                     num_speakers=(num_speakers if (num_speakers or 0) >= 1 else None)
                )
                
                # Merge diarization with transcript
                if diarization and diarization.segments:
                    transcript = self._merge_diarization(transcript, diarization)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Transcription completed for {audio_id} in {processing_time:.2f}s "
                       f"using {provider_name}")
            
            return TranscriptionResponse(
                success=True,
                transcript=transcript,
                diarization=diarization,
                processing_time_seconds=processing_time,
                provider=provider_name
            )
            
        except TranscriptionError as e:
            processing_time = time.time() - start_time
            logger.error(f"Transcription error for {audio_id}: {e.message}")
            return TranscriptionResponse(
                success=False,
                transcript=None,
                diarization=None,
                processing_time_seconds=processing_time,
                provider=provider_name,
                error=e.message
            )
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Unexpected transcription error for {audio_id}: {str(e)}", exc_info=True)
            return TranscriptionResponse(
                success=False,
                transcript=None,
                diarization=None,
                processing_time_seconds=processing_time,
                provider=provider_name,
                error=f"Transcription failed: {str(e)}"
            )
    
    async def _load_audio(self, audio_data_base64: str) -> Tuple[np.ndarray, int]:
        """
        Load audio from base64-encoded data.
        
        Args:
            audio_data_base64: Base64 encoded audio data
        
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            # Decode base64
            audio_bytes = base64.b64decode(audio_data_base64)
            
            # Check size limit
            if len(audio_bytes) > self.config.max_audio_size_bytes:
                raise TranscriptionError(
                    f"Audio data exceeds maximum size of {self.config.max_audio_size_mb}MB",
                    recoverable=False
                )
            
            # Try loading with soundfile first
            try:
                import soundfile as sf
                audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
                
                # Convert stereo to mono if needed
                if len(audio_data.shape) > 1:
                    audio_data = audio_data.mean(axis=1)
                
                # Convert to float32
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                
                return audio_data, sample_rate
                
            except Exception as sf_error:
                logger.debug(f"soundfile failed, trying librosa: {sf_error}")
            
            # Try librosa as fallback
            try:
                import librosa
                
                # Write to temp file for librosa
                fd, temp_path = tempfile.mkstemp(suffix='.audio', prefix='transcribe_load_')
                try:
                    os.close(fd)
                    with open(temp_path, 'wb') as f:
                        f.write(audio_bytes)
                    
                    audio_data, sample_rate = librosa.load(temp_path, sr=None, mono=True)
                    return audio_data.astype(np.float32), sample_rate
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
            except ImportError:
                raise TranscriptionError(
                    "Neither soundfile nor librosa available for audio loading",
                    recoverable=False
                )
                
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(
                f"Failed to load audio: {str(e)}",
                recoverable=False
            )
    
    def _get_provider(self, provider_name: str):
        """Get or create a provider instance."""
        if provider_name not in self._providers:
            self._providers[provider_name] = get_provider(provider_name)
        return self._providers[provider_name]
    
    def _merge_diarization(
        self,
        transcript: Transcript,
        diarization: DiarizationResult
    ) -> Transcript:
        """Merge diarization results into transcript segments."""
        if not diarization or not diarization.segments:
            return transcript
        
        # Convert transcript segments to dicts for merging
        segment_dicts = [
            {
                'start': seg.start_time,
                'end': seg.end_time,
                'text': seg.text,
                'confidence': seg.confidence,
                'speaker': seg.speaker
            }
            for seg in transcript.segments
        ]
        
        # Merge with diarization
        merged_dicts = self._diarizer.merge_transcript_with_diarization(
            segment_dicts,
            diarization.segments
        )
        
        # Create new transcript with merged segments
        from .models import TranscriptSegment
        
        new_segments = [
            TranscriptSegment(
                start_time=seg['start'],
                end_time=seg['end'],
                text=seg['text'],
                confidence=seg['confidence'],
                speaker=seg.get('speaker')
            )
            for seg in merged_dicts
        ]
        
        return Transcript(
            audio_id=transcript.audio_id,
            language=transcript.language,
            duration=transcript.duration,
            segments=new_segments,
            full_text=transcript.full_text
        )
    
    async def check_health(self) -> dict:
        """
        Check health of transcription services.
        
        Returns:
            Dict with health status for each provider
        """
        health = {
            "enabled": self.config.enabled,
            "demo_mode": self.config.demo_mode,
            "available_providers": self.config.get_available_providers(),
            "providers": {}
        }
        
        for provider_name in self.config.get_available_providers():
            try:
                provider = self._get_provider(provider_name)
                is_available = await provider.is_available()
                health["providers"][provider_name] = {
                    "available": is_available,
                    "healthy": provider.healthy
                }
            except Exception as e:
                health["providers"][provider_name] = {
                    "available": False,
                    "healthy": False,
                    "error": str(e)
                }
        
        return health
    
    def get_config(self) -> dict:
        """Get current configuration (safe for API exposure)."""
        return self.config.to_dict()


def get_transcriber(config: Optional[TranscriptionConfig] = None) -> Transcriber:
    """
    Get the transcriber singleton.
    
    Args:
        config: Optional config (only used on first call)
    
    Returns:
        Transcriber instance
    """
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber(config)
    return _transcriber


def reset_transcriber() -> None:
    """Reset the transcriber singleton (for testing)."""
    global _transcriber
    _transcriber = None
