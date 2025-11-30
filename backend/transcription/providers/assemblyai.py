"""
AssemblyAI Transcription Provider

Uses AssemblyAI's API for cloud-based transcription with advanced features.
Requires ASSEMBLYAI_API_KEY environment variable.
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

# Track if assemblyai is available
_assemblyai_available = None


def check_assemblyai_available() -> bool:
    """Check if assemblyai library is available."""
    global _assemblyai_available
    if _assemblyai_available is None:
        try:
            import assemblyai  # noqa: F401
            _assemblyai_available = True
            logger.info("AssemblyAI library is available")
        except ImportError:
            _assemblyai_available = False
            logger.warning("AssemblyAI library not installed. Install with: pip install assemblyai")
    return _assemblyai_available


class AssemblyAIProvider(TranscriptionProvider):
    """AssemblyAI transcription provider."""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "assemblyai"
        self._transcriber = None
    
    def _get_transcriber(self):
        """Get or create AssemblyAI transcriber."""
        if self._transcriber is not None:
            return self._transcriber
        
        if not check_assemblyai_available():
            raise TranscriptionError(
                "AssemblyAI library not installed",
                provider=self.name,
                recoverable=False
            )
        
        if not self.config.assemblyai_api_key:
            raise TranscriptionError(
                "AssemblyAI API key not configured",
                provider=self.name,
                recoverable=False
            )
        
        try:
            import assemblyai as aai
            aai.settings.api_key = self.config.assemblyai_api_key
            self._transcriber = aai.Transcriber()
            return self._transcriber
        except Exception as e:
            raise TranscriptionError(
                f"Failed to create AssemblyAI transcriber: {str(e)}",
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
        Transcribe audio using AssemblyAI API.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            language: Optional language code
            **kwargs: Additional options including audio_id, enable_diarization
        
        Returns:
            Transcript with segments and full text
        """
        audio_id = kwargs.get('audio_id', 'assemblyai-audio')
        enable_diarization = kwargs.get('enable_diarization', False)
        num_speakers = kwargs.get('num_speakers')
        temp_file_path = None
        
        try:
            transcriber = self._get_transcriber()
            
            # Calculate duration
            duration = len(audio_data) / sample_rate if sample_rate > 0 else 0
            
            # Create temporary WAV file for API upload
            # Using secure temporary file creation
            fd, temp_file_path = tempfile.mkstemp(suffix='.wav', prefix='transcribe_aai_')
            try:
                import soundfile as sf
                os.close(fd)  # Close the file descriptor before writing with soundfile
                sf.write(temp_file_path, audio_data, sample_rate)
            except ImportError:
                os.close(fd)
                raise TranscriptionError(
                    "soundfile library required for WAV export",
                    provider=self.name,
                    recoverable=False
                )
            
            # Prepare transcription config
            import assemblyai as aai
            
            config_params = {
                'punctuate': True,
                'format_text': True,
            }
            
            if language:
                config_params['language_code'] = language
            
            if enable_diarization:
                config_params['speaker_labels'] = True
                if num_speakers:
                    config_params['speakers_expected'] = num_speakers
            
            transcription_config = aai.TranscriptionConfig(**config_params)
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            
            def call_api():
                return transcriber.transcribe(temp_file_path, config=transcription_config)
            
            result = await asyncio.wait_for(
                loop.run_in_executor(None, call_api),
                timeout=self.config.assemblyai_timeout_seconds
            )
            
            # Check for errors
            if result.status == aai.TranscriptStatus.error:
                raise TranscriptionError(
                    f"AssemblyAI transcription failed: {result.error}",
                    provider=self.name,
                    recoverable=True
                )
            
            # Extract segments
            segments = []
            if result.utterances:
                # Use utterances if available (has speaker labels)
                for utterance in result.utterances:
                    segments.append({
                        'start': utterance.start / 1000.0,  # Convert ms to seconds
                        'end': utterance.end / 1000.0,
                        'text': utterance.text,
                        'confidence': utterance.confidence or 0.95,
                        'speaker': f"SPEAKER_{utterance.speaker}" if utterance.speaker else None
                    })
            elif result.words:
                # Fall back to words grouped into sentences
                current_segment = {'start': 0, 'end': 0, 'text': '', 'words': []}
                for word in result.words:
                    if not current_segment['text']:
                        current_segment['start'] = word.start / 1000.0
                    
                    current_segment['words'].append(word)
                    current_segment['end'] = word.end / 1000.0
                    current_segment['text'] += word.text + ' '
                    
                    # Split on sentence-ending punctuation
                    if word.text and word.text[-1] in '.!?':
                        segments.append({
                            'start': current_segment['start'],
                            'end': current_segment['end'],
                            'text': current_segment['text'].strip(),
                            'confidence': sum(w.confidence for w in current_segment['words']) / len(current_segment['words']) if current_segment['words'] else 0.95,
                            'speaker': None
                        })
                        current_segment = {'start': 0, 'end': 0, 'text': '', 'words': []}
                
                # Add remaining text
                if current_segment['text'].strip():
                    segments.append({
                        'start': current_segment['start'],
                        'end': current_segment['end'],
                        'text': current_segment['text'].strip(),
                        'confidence': sum(w.confidence for w in current_segment['words']) / len(current_segment['words']) if current_segment['words'] else 0.95,
                        'speaker': None
                    })
            else:
                # Fallback: single segment
                segments.append({
                    'start': 0,
                    'end': duration,
                    'text': result.text or '',
                    'confidence': 0.95,
                    'speaker': None
                })
            
            detected_language = result.language_code or language or 'en'
            
            logger.info(f"AssemblyAI transcription completed for {audio_id}: "
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
                f"AssemblyAI timeout after {self.config.assemblyai_timeout_seconds}s",
                provider=self.name,
                recoverable=True
            )
        except TranscriptionError:
            self.mark_failure()
            raise
        except Exception as e:
            self.mark_failure()
            logger.error(f"AssemblyAI transcription failed: {str(e)}", exc_info=True)
            raise TranscriptionError(
                f"AssemblyAI transcription failed: {str(e)}",
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
        """Check if AssemblyAI is available."""
        if not check_assemblyai_available():
            return False
        if not self.config.assemblyai_api_key:
            return False
        return self.healthy
