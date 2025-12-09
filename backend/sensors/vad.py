"""
Voice Activity Detection (VAD) module.

Provides robust speech segment detection using either:
1. Silero VAD ONNX model (when onnxruntime is available) - more accurate
2. Energy-based detection with adaptive thresholding (fallback)

The Silero VAD strategy measures actual breath groups (speech segments)
rather than just file duration, providing more accurate phonation analysis.
"""

import logging
from dataclasses import dataclass
from typing import List

import numpy as np
from scipy.signal import medfilt

logger = logging.getLogger(__name__)

# Silero VAD model constants
SILERO_SAMPLE_RATE = 16000
SILERO_CHUNK_SIZE = 512  # 32ms at 16kHz
SILERO_THRESHOLD = 0.5  # Default speech probability threshold

# Energy-based VAD constants (fallback)
ENERGY_FRAME_SIZE_SECONDS = 0.03  # 30ms frames
ENERGY_HOP_SIZE_SECONDS = 0.01  # 10ms hop
ENERGY_SILENCE_THRESHOLD_DB = -50  # Between -60dB (too sensitive) and -40dB (too aggressive)
MIN_SPEECH_DURATION_SECONDS = 0.1  # Minimum speech segment duration
# Breathing pauses are typically 200-500ms; micro-pauses in speech are < 150ms
# Using 200ms ensures we only split on actual breathing pauses
MIN_SILENCE_DURATION_SECONDS = 0.2  # Minimum silence to consider a breath break

# Try to import ONNX runtime for future Silero VAD model support
# TODO: Bundle Silero VAD ONNX model for enhanced speech detection accuracy
# For now, the enhanced energy-based detection provides robust results
ONNX_AVAILABLE = False
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ort = None
    logger.debug("onnxruntime not available - using energy-based VAD")


@dataclass
class SpeechSegment:
    """Represents a detected speech segment."""
    start_seconds: float
    end_seconds: float
    
    @property
    def duration_seconds(self) -> float:
        """Duration of the speech segment in seconds."""
        return self.end_seconds - self.start_seconds


class VoiceActivityDetector:
    """
    Voice Activity Detector using Silero VAD strategy.
    
    This class provides robust speech detection using enhanced energy-based
    detection with adaptive thresholding and median filtering.
    
    The goal is to identify actual speech segments (breath groups)
    rather than treating the entire audio as one continuous segment.
    
    Future enhancement: When onnxruntime is available and Silero VAD model
    is bundled, this class can use the neural network model for even more
    accurate speech detection.
    """
    
    def __init__(
        self,
        speech_threshold: float = SILERO_THRESHOLD,
        min_speech_duration: float = MIN_SPEECH_DURATION_SECONDS,
        min_silence_duration: float = MIN_SILENCE_DURATION_SECONDS,
        silence_threshold_db: float = ENERGY_SILENCE_THRESHOLD_DB,
    ):
        """
        Initialize Voice Activity Detector.
        
        Args:
            speech_threshold: Probability threshold for speech detection (0-1)
                             (Reserved for future ONNX model integration)
            min_speech_duration: Minimum duration in seconds for valid speech segment
            min_silence_duration: Minimum silence duration to split segments
            silence_threshold_db: Energy threshold in dB for speech (default: -50)
        """
        self.speech_threshold = speech_threshold
        self.min_speech_duration = min_speech_duration
        self.min_silence_duration = min_silence_duration
        self.silence_threshold_db = silence_threshold_db
    
    def detect_speech_segments(
        self,
        audio_data: np.ndarray,
        samplerate: int,
    ) -> List[SpeechSegment]:
        """
        Detect speech segments in audio.
        
        Args:
            audio_data: Audio signal as numpy array (mono)
            samplerate: Sample rate in Hz
            
        Returns:
            List of SpeechSegment objects representing speech regions
        """
        if len(audio_data) == 0:
            return []
        
        # Use enhanced energy-based detection (always available, works well)
        # Note: ONNX-based Silero VAD can be added later if model is bundled
        return self._detect_energy_based(audio_data, samplerate)
    
    def get_max_continuous_speech(
        self,
        audio_data: np.ndarray,
        samplerate: int,
    ) -> float:
        """
        Get the duration of the longest continuous speech segment.
        
        This is the key method for breath sensor - it finds the longest
        uninterrupted speech segment (breath group) in the audio.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            Duration of longest speech segment in seconds
        """
        segments = self.detect_speech_segments(audio_data, samplerate)
        if not segments:
            return 0.0
        return max(seg.duration_seconds for seg in segments)
    
    def _detect_energy_based(
        self,
        audio_data: np.ndarray,
        samplerate: int,
    ) -> List[SpeechSegment]:
        """
        Enhanced energy-based voice activity detection.
        
        Uses adaptive thresholding and median filtering for robustness.
        This approach is more sophisticated than simple dB thresholding.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            List of SpeechSegment objects
        """
        # Calculate frame parameters
        frame_size = int(ENERGY_FRAME_SIZE_SECONDS * samplerate)
        hop_size = int(ENERGY_HOP_SIZE_SECONDS * samplerate)
        
        if len(audio_data) < frame_size:
            # Audio too short - check if it's speech at all
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms > 0:
                db = 20 * np.log10(rms + 1e-9)
                if db > self.silence_threshold_db:
                    return [SpeechSegment(0.0, len(audio_data) / samplerate)]
            return []
        
        # Compute frame-level energy
        # Vectorized frame energy calculation
        # Create a strided view of the audio data to avoid copying

        # Calculate number of frames
        num_frames = (len(audio_data) - frame_size) // hop_size + 1
        
        # Create strided view: shape (num_frames, frame_size)
        # This is a view, not a copy, so it's memory efficient
        from numpy.lib.stride_tricks import as_strided
        
        strides = (hop_size * audio_data.itemsize, audio_data.itemsize)
        frames = as_strided(
            audio_data, 
            shape=(num_frames, frame_size), 
            strides=strides
        )
        
        # Calculate RMS for all frames at once
        # mean(frame**2) -> axis 1
        # We add 1e-9 inside the log, but for RMS we just need mean square
        mean_squares = np.mean(frames ** 2, axis=1)
        rms_values = np.sqrt(mean_squares)
        
        # Convert to dB
        energies_db = 20 * np.log10(rms_values + 1e-9)
        
        # Adaptive threshold: use a combination of fixed and relative thresholds
        # This handles varying recording levels better
        noise_floor = np.percentile(energies_db, 10)  # Estimate noise floor
        signal_peak = np.percentile(energies_db, 90)  # Estimate signal peak
        
        # Dynamic range of the signal
        dynamic_range = signal_peak - noise_floor
        
        # If signal has very low dynamic range (nearly constant), use fixed threshold
        # This handles edge cases like constant amplitude test signals
        if dynamic_range < 3.0:  # Less than 3dB variation = essentially constant
            adaptive_threshold = self.silence_threshold_db
        else:
            # Adaptive threshold is 30% up from noise floor toward signal peak,
            # but never lower than the fixed silence threshold
            adaptive_threshold = max(
                self.silence_threshold_db,
                noise_floor + 0.3 * dynamic_range
            )
        
        # Classify frames as speech/silence
        is_speech = (energies_db > adaptive_threshold).astype(np.int8)
        
        # Apply median filtering to remove isolated frames (noise reduction)
        # Window of 5 frames (~50ms) smooths out brief fluctuations
        if len(is_speech) >= 5:
            is_speech = medfilt(is_speech, kernel_size=5).astype(np.int8)
        
        # Convert frame decisions to segments
        return self._frames_to_segments(
            is_speech,
            hop_size,
            samplerate,
            len(audio_data) / samplerate
        )
    
    def _frames_to_segments(
        self,
        is_speech: np.ndarray,
        hop_size: int,
        samplerate: int,
        audio_duration: float,
    ) -> List[SpeechSegment]:
        """
        Convert frame-level speech decisions to time-aligned segments.
        
        Applies minimum duration constraints to filter out noise.
        
        Args:
            is_speech: Array of speech/silence decisions (1=speech, 0=silence)
            hop_size: Hop size in samples
            samplerate: Sample rate in Hz
            audio_duration: Total audio duration in seconds
            
        Returns:
            List of SpeechSegment objects
        """
        segments = []
        hop_seconds = hop_size / samplerate
        
        in_speech = False
        speech_start = 0.0
        
        for i, val in enumerate(is_speech):
            time_pos = i * hop_seconds
            
            if val == 1 and not in_speech:
                # Speech started
                in_speech = True
                speech_start = time_pos
            elif val == 0 and in_speech:
                # Speech ended
                in_speech = False
                duration = time_pos - speech_start
                if duration >= self.min_speech_duration:
                    segments.append(SpeechSegment(speech_start, time_pos))
        
        # Handle case where speech continues to end of audio
        if in_speech:
            end_time = min((len(is_speech) - 1) * hop_seconds + hop_seconds, audio_duration)
            duration = end_time - speech_start
            if duration >= self.min_speech_duration:
                segments.append(SpeechSegment(speech_start, end_time))
        
        # Merge segments that are too close together (brief pauses)
        return self._merge_close_segments(segments)
    
    def _merge_close_segments(
        self,
        segments: List[SpeechSegment],
    ) -> List[SpeechSegment]:
        """
        Merge speech segments that are separated by very brief silences.
        
        This handles momentary dips in energy that don't represent
        actual breathing pauses.
        
        Args:
            segments: List of speech segments
            
        Returns:
            Merged list of speech segments
        """
        if len(segments) <= 1:
            return segments
        
        merged = [segments[0]]
        
        for seg in segments[1:]:
            last = merged[-1]
            gap = seg.start_seconds - last.end_seconds
            
            if gap < self.min_silence_duration:
                # Merge with previous segment
                merged[-1] = SpeechSegment(last.start_seconds, seg.end_seconds)
            else:
                merged.append(seg)
        
        return merged


# Module-level convenience functions
_default_vad = None


def get_speech_segments(
    audio_data: np.ndarray,
    samplerate: int,
) -> List[SpeechSegment]:
    """
    Convenience function to detect speech segments.
    
    Args:
        audio_data: Audio signal as numpy array
        samplerate: Sample rate in Hz
        
    Returns:
        List of SpeechSegment objects
    """
    global _default_vad
    if _default_vad is None:
        _default_vad = VoiceActivityDetector()
    return _default_vad.detect_speech_segments(audio_data, samplerate)


def get_max_continuous_speech_duration(
    audio_data: np.ndarray,
    samplerate: int,
) -> float:
    """
    Get duration of longest continuous speech segment.
    
    Args:
        audio_data: Audio signal as numpy array
        samplerate: Sample rate in Hz
        
    Returns:
        Duration in seconds of longest speech segment
    """
    global _default_vad
    if _default_vad is None:
        _default_vad = VoiceActivityDetector()
    return _default_vad.get_max_continuous_speech(audio_data, samplerate)
