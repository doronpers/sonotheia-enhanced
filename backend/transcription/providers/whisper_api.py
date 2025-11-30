"""
OpenAI Whisper API Transcription Provider

Uses OpenAI's Whisper API for cloud-based transcription.
Requires OPENAI_API_KEY environment variable.
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

# Track if openai is available
_openai_available = None


def check_openai_available() -> bool:
    """Check if openai library is available."""
    global _openai_available
    if _openai_available is None:
        try:
            import openai  # noqa: F401
            _openai_available = True
            logger.info("OpenAI library is available")
        except ImportError:
            _openai_available = False
            logger.warning("OpenAI library not installed. Install with: pip install openai")
    return _openai_available


class WhisperAPIProvider(TranscriptionProvider):
    """OpenAI Whisper API transcription provider."""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "whisper_api"
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is not None:
            return self._client
        
        if not check_openai_available():
            raise TranscriptionError(
                "OpenAI library not installed",
                provider=self.name,
                recoverable=False
            )
        
        if not self.config.openai_api_key:
            raise TranscriptionError(
                "OpenAI API key not configured",
                provider=self.name,
                recoverable=False
            )
        
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.config.openai_api_key)
            return self._client
        except Exception as e:
            raise TranscriptionError(
                f"Failed to create OpenAI client: {str(e)}",
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
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            language: Optional language code
            **kwargs: Additional options including audio_id
        
        Returns:
            Transcript with segments and full text
        """
        audio_id = kwargs.get('audio_id', 'whisper-api-audio')
        temp_file_path = None
        
        try:
            client = self._get_client()
            
            # Calculate duration
            duration = len(audio_data) / sample_rate if sample_rate > 0 else 0
            
            # Create temporary WAV file for API upload
            # Using secure temporary file creation
            fd, temp_file_path = tempfile.mkstemp(suffix='.wav', prefix='transcribe_')
            try:
                import soundfile as sf
                # Write audio to temp file
                os.close(fd)  # Close the file descriptor before writing with soundfile
                sf.write(temp_file_path, audio_data, sample_rate)
            except ImportError:
                os.close(fd)
                raise TranscriptionError(
                    "soundfile library required for WAV export",
                    provider=self.name,
                    recoverable=False
                )
            
            # Prepare API call options
            transcription_params = {
                'model': self.config.openai_model,
                'response_format': 'verbose_json',
                'timestamp_granularities': ['segment']
            }
            
            if language:
                transcription_params['language'] = language
            
            # Run API call in thread pool
            loop = asyncio.get_event_loop()
            
            def call_api():
                with open(temp_file_path, 'rb') as audio_file:
                    return client.audio.transcriptions.create(
                        file=audio_file,
                        **transcription_params
                    )
            
            result = await asyncio.wait_for(
                loop.run_in_executor(None, call_api),
                timeout=self.config.openai_timeout_seconds
            )
            
            # Extract segments
            segments = []
            if hasattr(result, 'segments') and result.segments:
                for seg in result.segments:
                    segments.append({
                        'start': seg.get('start', 0),
                        'end': seg.get('end', 0),
                        'text': seg.get('text', ''),
                        'confidence': 0.95,  # API doesn't return confidence
                        'speaker': None
                    })
            else:
                # Fallback: create single segment from full text
                segments.append({
                    'start': 0,
                    'end': duration,
                    'text': result.text,
                    'confidence': 0.95,
                    'speaker': None
                })
            
            detected_language = getattr(result, 'language', language or 'en')
            
            logger.info(f"Whisper API transcription completed for {audio_id}: "
                       f"{duration:.2f}s, {len(segments)} segments, lang={detected_language}")
            
            self.mark_success()
            
            return self._create_transcript(
                audio_id=audio_id,
                segments=segments,
                language=detected_language,
                duration=duration
            )
            
        except asyncio.TimeoutError:
            self.mark_failure()
            raise TranscriptionError(
                f"Whisper API timeout after {self.config.openai_timeout_seconds}s",
                provider=self.name,
                recoverable=True
            )
        except TranscriptionError:
            self.mark_failure()
            raise
        except Exception as e:
            self.mark_failure()
            logger.error(f"Whisper API transcription failed: {str(e)}", exc_info=True)
            raise TranscriptionError(
                f"Whisper API transcription failed: {str(e)}",
                provider=self.name,
                recoverable=True
            )
        finally:
            # Clean up temp file
            if temp_file_path and self.config.cleanup_temp_files:
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
    
    async def is_available(self) -> bool:
        """Check if Whisper API is available."""
        if not check_openai_available():
            return False
        if not self.config.openai_api_key:
            return False
        return self.healthy
