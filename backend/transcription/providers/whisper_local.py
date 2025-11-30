"""
Local Whisper Transcription Provider

Uses OpenAI's Whisper model locally for privacy-sensitive deployments.
Falls back to demo mode if Whisper is not installed.
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional
import numpy as np

from .base import TranscriptionProvider, TranscriptionError
from ..models import Transcript

logger = logging.getLogger(__name__)

# Track if whisper is available
_whisper_available = None


def check_whisper_available() -> bool:
    """Check if whisper library is available."""
    global _whisper_available
    if _whisper_available is None:
        try:
            import whisper  # noqa: F401
            _whisper_available = True
            logger.info("Whisper library is available")
        except ImportError:
            _whisper_available = False
            logger.warning("Whisper library not installed. Install with: pip install openai-whisper")
    return _whisper_available


class WhisperLocalProvider(TranscriptionProvider):
    """Local Whisper transcription provider."""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "whisper_local"
        self._model = None
        self._model_name = config.whisper_model_size
        self._device = config.whisper_device
    
    def _load_model(self):
        """Load Whisper model lazily."""
        if self._model is not None:
            return self._model
        
        if not check_whisper_available():
            raise TranscriptionError(
                "Whisper library not installed",
                provider=self.name,
                recoverable=False
            )
        
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self._model_name} on {self._device}")
            self._model = whisper.load_model(self._model_name, device=self._device)
            logger.info(f"Whisper model loaded successfully")
            return self._model
        except Exception as e:
            raise TranscriptionError(
                f"Failed to load Whisper model: {str(e)}",
                provider=self.name,
                recoverable=False
            )
    
    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None,
        **kwargs
    ) -> Transcript:
        """
        Transcribe audio using local Whisper model.
        
        Args:
            audio_data: Audio samples as numpy array (mono, float32)
            sample_rate: Sample rate in Hz
            language: Optional language code (auto-detect if None)
            **kwargs: Additional options including audio_id
        
        Returns:
            Transcript with segments and full text
        """
        audio_id = kwargs.get('audio_id', 'whisper-audio')
        
        try:
            # If whisper not available, fall back to demo mode
            if not check_whisper_available():
                logger.warning("Whisper not available, using demo mode")
                from .demo import DemoProvider
                demo = DemoProvider(self.config)
                return await demo.transcribe(audio_data, sample_rate, language, **kwargs)
            
            model = self._load_model()
            
            # Ensure audio is float32 and mono
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Resample to 16kHz if needed (Whisper requires 16kHz)
            if sample_rate != 16000:
                audio_data = self._resample(audio_data, sample_rate, 16000)
                sample_rate = 16000
            
            # Normalize audio
            if np.abs(audio_data).max() > 1.0:
                audio_data = audio_data / np.abs(audio_data).max()
            
            duration = len(audio_data) / sample_rate
            
            # Prepare transcription options
            options = {
                'verbose': False,
                'task': 'transcribe',
            }
            
            if language:
                options['language'] = language
            
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: model.transcribe(audio_data, **options)
            )
            
            # Extract segments
            segments = []
            for seg in result.get('segments', []):
                segments.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': seg['text'],
                    'confidence': seg.get('avg_logprob', 0) + 1,  # Convert logprob to ~confidence
                    'speaker': None
                })
            
            detected_language = result.get('language', language or 'en')
            
            logger.info(f"Whisper transcription completed for {audio_id}: "
                       f"{duration:.2f}s, {len(segments)} segments, lang={detected_language}")
            
            self.mark_success()
            
            return self._create_transcript(
                audio_id=audio_id,
                segments=segments,
                language=detected_language,
                duration=duration
            )
            
        except TranscriptionError:
            self.mark_failure()
            raise
        except Exception as e:
            self.mark_failure()
            logger.error(f"Whisper transcription failed: {str(e)}", exc_info=True)
            raise TranscriptionError(
                f"Whisper transcription failed: {str(e)}",
                provider=self.name,
                recoverable=True
            )
    
    async def is_available(self) -> bool:
        """Check if Whisper is available."""
        if not check_whisper_available():
            return False
        return self.healthy
    
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        try:
            import librosa
            return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        except ImportError:
            # Simple linear interpolation fallback
            ratio = target_sr / orig_sr
            new_length = int(len(audio) * ratio)
            indices = np.linspace(0, len(audio) - 1, new_length)
            return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
