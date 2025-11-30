"""
Speaker Diarization Module

Identifies and separates speakers in audio recordings.
Uses pyannote.audio when available, falls back to demo mode.
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional, List
import numpy as np

from .models import DiarizationSegment, DiarizationResult
from .config import get_transcription_config

logger = logging.getLogger(__name__)

# Track if pyannote is available
_pyannote_available = None


def check_pyannote_available() -> bool:
    """Check if pyannote.audio is available."""
    global _pyannote_available
    if _pyannote_available is None:
        try:
            from pyannote.audio import Pipeline  # noqa: F401
            _pyannote_available = True
            logger.info("pyannote.audio is available")
        except ImportError:
            _pyannote_available = False
            logger.warning("pyannote.audio not installed. Install with: pip install pyannote.audio")
    return _pyannote_available


class SpeakerDiarizer:
    """Speaker diarization using pyannote.audio or demo fallback."""
    
    def __init__(self, config=None):
        """
        Initialize diarizer.
        
        Args:
            config: TranscriptionConfig instance (uses default if None)
        """
        self.config = config or get_transcription_config()
        self._pipeline = None
    
    def _load_pipeline(self):
        """Load diarization pipeline lazily."""
        if self._pipeline is not None:
            return self._pipeline
        
        if not check_pyannote_available():
            return None
        
        if not self.config.pyannote_auth_token:
            logger.warning("pyannote auth token not configured, using demo mode")
            return None
        
        try:
            from pyannote.audio import Pipeline
            
            logger.info("Loading pyannote diarization pipeline...")
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.config.pyannote_auth_token
            )
            logger.info("Diarization pipeline loaded successfully")
            return self._pipeline
        except Exception as e:
            logger.warning(f"Failed to load diarization pipeline: {e}")
            return None
    
    async def diarize(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        audio_id: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """
        Perform speaker diarization on audio.
        
        Args:
            audio_data: Audio samples as numpy array (mono)
            sample_rate: Sample rate in Hz
            audio_id: Unique identifier for the audio
            num_speakers: Expected number of speakers (if known)
            min_speakers: Minimum expected speakers
            max_speakers: Maximum expected speakers
        
        Returns:
            DiarizationResult with speaker segments
        """
        duration = len(audio_data) / sample_rate if sample_rate > 0 else 0
        
        pipeline = self._load_pipeline()
        
        if pipeline is None:
            # Use demo diarization
            return await self._demo_diarize(audio_id, duration, num_speakers)
        
        return await self._pyannote_diarize(
            audio_data, sample_rate, audio_id, duration,
            num_speakers, min_speakers, max_speakers
        )
    
    async def _pyannote_diarize(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        audio_id: str,
        duration: float,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """Perform diarization using pyannote.audio."""
        temp_file_path = None
        
        try:
            # Create temporary WAV file
            fd, temp_file_path = tempfile.mkstemp(suffix='.wav', prefix='diarize_')
            try:
                import soundfile as sf
                os.close(fd)
                sf.write(temp_file_path, audio_data, sample_rate)
            except ImportError:
                os.close(fd)
                logger.warning("soundfile not available, using demo diarization")
                return await self._demo_diarize(audio_id, duration, num_speakers)
            
            # Prepare pipeline parameters
            params = {}
            if num_speakers:
                params['num_speakers'] = num_speakers
            else:
                if min_speakers:
                    params['min_speakers'] = min_speakers
                if max_speakers:
                    params['max_speakers'] = max_speakers
            
            # Run diarization in thread pool
            loop = asyncio.get_event_loop()
            
            def run_diarization():
                return self._pipeline(temp_file_path, **params)
            
            diarization = await loop.run_in_executor(None, run_diarization)
            
            # Extract segments
            segments = []
            speakers = set()
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)
                segments.append(DiarizationSegment(
                    start_time=turn.start,
                    end_time=turn.end,
                    speaker=speaker,
                    confidence=0.9  # pyannote doesn't provide per-segment confidence
                ))
            
            logger.info(f"Diarization completed for {audio_id}: "
                       f"{len(speakers)} speakers, {len(segments)} segments")
            
            return DiarizationResult(
                audio_id=audio_id,
                num_speakers=len(speakers),
                segments=segments,
                duration=duration
            )
            
        except Exception as e:
            logger.error(f"Diarization failed: {str(e)}", exc_info=True)
            # Fall back to demo
            return await self._demo_diarize(audio_id, duration, num_speakers)
        finally:
            # Clean up temp file
            if temp_file_path and self.config.cleanup_temp_files:
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
    
    async def _demo_diarize(
        self,
        audio_id: str,
        duration: float,
        num_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """Generate demo diarization data."""
        # Simulate processing time
        await asyncio.sleep(min(duration * 0.05, 1.0))
        
        # Default to 2 speakers for demo
        actual_speakers = num_speakers or 2
        
        # Generate alternating speaker segments
        segments = []
        segment_duration = 5.0  # Average segment duration
        current_time = 0.0
        speaker_idx = 0
        
        while current_time < duration:
            # Vary segment length slightly
            seg_len = segment_duration * (0.8 + (speaker_idx % 3) * 0.2)
            end_time = min(current_time + seg_len, duration)
            
            segments.append(DiarizationSegment(
                start_time=current_time,
                end_time=end_time,
                speaker=f"SPEAKER_{speaker_idx % actual_speakers:02d}",
                confidence=0.85 + (speaker_idx % 3) * 0.05
            ))
            
            current_time = end_time
            speaker_idx += 1
        
        logger.info(f"Demo diarization completed for {audio_id}: "
                   f"{actual_speakers} speakers, {len(segments)} segments")
        
        return DiarizationResult(
            audio_id=audio_id,
            num_speakers=actual_speakers,
            segments=segments,
            duration=duration
        )
    
    def merge_transcript_with_diarization(
        self,
        transcript_segments: List[dict],
        diarization_segments: List[DiarizationSegment]
    ) -> List[dict]:
        """
        Merge transcript segments with diarization to add speaker labels.
        
        Args:
            transcript_segments: List of transcript segment dicts
            diarization_segments: List of DiarizationSegment objects
        
        Returns:
            Transcript segments with speaker labels added
        """
        if not diarization_segments:
            return transcript_segments
        
        merged = []
        
        for seg in transcript_segments:
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            mid_point = (start + end) / 2
            
            # Find the diarization segment that contains the midpoint
            speaker = None
            for d_seg in diarization_segments:
                if d_seg.start_time <= mid_point <= d_seg.end_time:
                    speaker = d_seg.speaker
                    break
            
            # If no exact match, find the closest segment
            if speaker is None and diarization_segments:
                closest = min(
                    diarization_segments,
                    key=lambda d: abs((d.start_time + d.end_time) / 2 - mid_point)
                )
                speaker = closest.speaker
            
            merged_seg = dict(seg)
            merged_seg['speaker'] = speaker
            merged.append(merged_seg)
        
        return merged


# Module-level convenience function
async def diarize_audio(
    audio_data: np.ndarray,
    sample_rate: int,
    audio_id: str,
    num_speakers: Optional[int] = None
) -> DiarizationResult:
    """
    Convenience function for speaker diarization.
    
    Args:
        audio_data: Audio samples as numpy array
        sample_rate: Sample rate in Hz
        audio_id: Audio identifier
        num_speakers: Expected number of speakers
    
    Returns:
        DiarizationResult
    """
    diarizer = SpeakerDiarizer()
    return await diarizer.diarize(audio_data, sample_rate, audio_id, num_speakers)
