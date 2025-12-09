"""
Breath sensor for detecting biologically impossible phonation patterns.

Detects continuous speech segments that exceed human respiratory capabilities.
Uses robust Voice Activity Detection (VAD) to identify actual breath groups,
rather than treating the entire audio file as one continuous segment.

Also implements "Respiration Monitor" to detect "Infinite Lung Capacity" violations:
Humans must pause to inhale. The maximum duration a human can sustain continuous
speech (Maximum Phonation Duration) is physiologically limited by lung volume and
airflow rates. TTS systems operate with "No biological constraints on speech duration"
and can generate run-on sentences or 30-second flows of speech with zero intake breaths.
"""

from typing import Dict
import numpy as np
from .base import BaseSensor, SensorResult
from .vad import VoiceActivityDetector
from backend.utils.config import get_threshold

# Constants - can be overridden by config/settings.yaml
MAX_PHONATION_SECONDS = get_threshold("breath", "max_phonation_seconds", 14.0)
# Respiration monitoring threshold: maximum continuous voiced segment without breath event
MAX_VOICED_WITHOUT_BREATH_SECONDS = get_threshold("breath", "max_voiced_without_breath_seconds", 15.0)
MIN_BREATH_SILENCE_SECONDS = 0.2  # Minimum silence duration to count as breath event (200ms)
# Legacy constants for backward compatibility - kept as constructor defaults
# The VAD module uses adaptive thresholding for more robust detection
SILENCE_THRESHOLD_DB = get_threshold("breath", "silence_threshold_db", -60)
FRAME_SIZE_SECONDS = get_threshold("breath", "frame_size_seconds", 0.02)


class BreathSensor(BaseSensor):
    """
    Breath sensor that checks for biologically impossible phonation patterns.
    
    Analyzes audio for maximum continuous speech duration. Human speech
    cannot sustain continuous phonation beyond ~14 seconds due to respiratory
    limitations. AI-generated audio may exceed this limit.
    
    Uses a robust Voice Activity Detection (VAD) approach to identify
    actual speech segments (breath groups) separated by silence/pauses.
    This provides more accurate phonation measurement than simple
    energy-based thresholding across the entire file duration.
    
    Also implements "Respiration Monitor" to detect "Infinite Lung Capacity" violations:
    Tracks the duration of continuous "voiced" segments and flags if a segment exceeds
    ~15 seconds without a detectable "breath event" (inhalation noise or silence >200ms).
    This works best in "Full Analysis" mode as it requires analyzing longer context windows.
    """
    
    def __init__(
        self,
        max_phonation_seconds: float = MAX_PHONATION_SECONDS,
        silence_threshold_db: float = SILENCE_THRESHOLD_DB,
        frame_size_seconds: float = FRAME_SIZE_SECONDS,
        category: str = "defense"
    ):
        """
        Initialize breath sensor.
        
        Args:
            max_phonation_seconds: Maximum allowed continuous phonation (default: 14.0s)
            silence_threshold_db: Energy threshold for speech detection (default: -60dB)
                                  Note: The VAD module uses adaptive thresholding for
                                  more robust detection.
            frame_size_seconds: Frame size for analysis (default: 0.02s)
            category: "prosecution" or "defense"
        """
        super().__init__("Breath Sensor (Max Phonation)", category=category)
        self.max_phonation_seconds = max_phonation_seconds
        self.silence_threshold_db = silence_threshold_db
        self.frame_size_seconds = frame_size_seconds
        # Initialize VAD with settings appropriate for breath detection
        # Minimum silence of 200ms ensures we only split on actual breathing pauses,
        # not brief micro-pauses that naturally occur in continuous speech
        self._vad = VoiceActivityDetector(
            speech_threshold=0.5,
            min_speech_duration=0.1,  # 100ms minimum speech segment
            min_silence_duration=0.2,  # 200ms silence = actual breath break
        )
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for maximum continuous phonation duration.
        
        Uses robust VAD to detect speech segments and find the longest
        continuous breath group (speech segment between pauses).
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with phonation duration analysis
        """
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=0.0,
                threshold=self.max_phonation_seconds,
                detail="Invalid or empty audio input."
            )
        
        frame_size = int(self.frame_size_seconds * samplerate)
        if len(audio_data) < frame_size:
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=0.0,
                threshold=self.max_phonation_seconds,
                detail="Audio too short for analysis."
            )
        
        # Use robust VAD to find speech segments (breath groups)
        
        # Autonomous Tuning: Calculate dynamic noise threshold
        noise_floor_db = self._calculate_noise_floor(audio_data)
        
        # Default safety: default to configured hard threshold if noise floor is absurdly low (digital silence)
        # or absurdly high (constant loud noise).
        # Otherwise, adapt: silence = noise_floor + 10dB (10dB SNR assumption for speech onset)
        tuned_threshold = self.silence_threshold_db
        
        if -80 < noise_floor_db < -30:
            tuned_threshold = max(self.silence_threshold_db, noise_floor_db + 10.0)
            
        # Create a temporary VAD instance with the tuned threshold for this specific analysis
        # (This is lightweight)
        vad = VoiceActivityDetector(
            speech_threshold=0.5,
            min_speech_duration=0.1,
            min_silence_duration=0.2,
            silence_threshold_db=tuned_threshold
        )
        
        max_duration = vad.get_max_continuous_speech(audio_data, samplerate)
        max_duration = round(float(max_duration), 2)
        
        # Respiration monitoring: detect "Infinite Lung Capacity" violations
        respiration_results = self._monitor_respiration(audio_data, samplerate)
        
        # Check both max phonation duration and respiration violations
        passed_phonation = bool(max_duration <= self.max_phonation_seconds)
        passed_respiration = not respiration_results.get("has_violation", False)
        passed = passed_phonation and passed_respiration
        
        result = SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=max_duration,
            threshold=self.max_phonation_seconds,
        )
        
        if not passed:
            if not passed_phonation:
                result.reason = "BIOLOGICALLY_IMPOSSIBLE"
                result.detail = f"Phonation duration of {max_duration}s exceeds biological limit."
            elif not passed_respiration:
                result.reason = "INFINITE_LUNG_CAPACITY"
                max_voiced = respiration_results.get("max_voiced_without_breath", 0.0)
                result.detail = (
                    f"Superhuman phonation duration: {max_voiced:.1f}s continuous voiced segment "
                    f"without detectable breath event (max: {MAX_VOICED_WITHOUT_BREATH_SECONDS}s). "
                    f"Indicates synthetic audio with no biological constraints on speech duration."
                )
                
        # Calculate normalized anomaly score (0.0 = Real, 1.0 = Fake)
        # Soft sigmoid around threshold
        # If max_duration is 8s (well below 14s), score should be low.
        # If max_duration is 16s (above 14s), score should be high.
        deviation = max_duration - self.max_phonation_seconds
        # Map deviation: -5s -> 0.0, 0s -> 0.5, +5s -> 1.0
        normalized_score = 1.0 / (1.0 + np.exp(-deviation))
        
        result.score = float(normalized_score) # Explicit score for FusionEngine
        
        # Add respiration monitoring metadata
        result.metadata = {
            "max_phonation_seconds": max_duration,
            "respiration_violation": respiration_results.get("has_violation", False),
            "max_voiced_without_breath_seconds": round(
                respiration_results.get("max_voiced_without_breath", 0.0), 2
            ),
            "breath_event_count": respiration_results.get("breath_event_count", 0),
        }
        
        return result
    
    def _calculate_noise_floor(self, audio_data: np.ndarray, frame_duration: float = 0.1) -> float:
        """
        Calculate the noise floor of the audio.
        
        Uses the 10th percentile of frame RMS energy as the noise floor estimate.
        
        Args:
            audio_data: Audio signal
            frame_duration: Duration of analysis frames in seconds
            
        Returns:
            Noise floor in dB
        """
        # Quick RMS calculation on frames
        frame_size = int(frame_duration * 16000)  # Assume 16k or adjust if needed
        # Just use simple strided view for speed estimate (don't need perfect hop)
        if len(audio_data) < frame_size:
            rms = np.sqrt(np.mean(audio_data**2))
            return 20 * np.log10(rms + 1e-9)
            
        # Reshape to roughly frame_size chunks (discard remainder for speed)
        num_frames = len(audio_data) // frame_size
        if num_frames == 0:
            return -60.0 # Default
            
        frames = audio_data[:num_frames * frame_size].reshape(num_frames, frame_size)
        rms_values = np.sqrt(np.mean(frames**2, axis=1))
        db_values = 20 * np.log10(rms_values + 1e-9)
        
        # 10th percentile captures the quietest parts (background noise)
        return np.percentile(db_values, 10)
    
    def _monitor_respiration(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> Dict:
        """
        Monitor respiration to detect "Infinite Lung Capacity" violations.
        
        The Physics: Humans must pause to inhale. The maximum duration a human can
        sustain continuous speech (Maximum Phonation Duration) is physiologically limited
        by lung volume and airflow rates.
        
        The Violation: TTS systems operate with "No biological constraints on speech duration".
        They can generate run-on sentences or 30-second flows of speech with zero intake breaths.
        
        Implementation: Track the duration of continuous "voiced" segments (using VAD or
        pitch tracking). If a voiced segment exceeds ~15 seconds without a detectable "breath
        event" (inhalation noise or silence >200ms), flag as "Superhuman Phonation Duration."
        
        Args:
            audio: Audio signal
            sr: Sample rate in Hz
            
        Returns:
            Dictionary with respiration monitoring results
        """
        # Use VAD to find speech segments
        
        # Similar tuning logic (could refactor to shared method, but keeping localized for now)
        noise_floor_db = self._calculate_noise_floor(audio)
        tuned_threshold = self.silence_threshold_db
        if -80 < noise_floor_db < -30:
            tuned_threshold = max(self.silence_threshold_db, noise_floor_db + 10.0)
            
        vad = VoiceActivityDetector(
            speech_threshold=0.5,
            min_speech_duration=0.1,
            min_silence_duration=0.2,
            silence_threshold_db=tuned_threshold
        )
        
        segments = vad.detect_speech_segments(audio, sr)
        
        if not segments:
            return {
                "has_violation": False,
                "max_voiced_without_breath": 0.0,
                "breath_event_count": 0,
            }
        
        total_duration = len(audio) / sr
        
        # Track continuous voiced segments without breath breaks
        max_voiced_without_breath = 0.0
        breath_event_count = 0
        
        # Process segments and gaps between them
        for i, segment in enumerate(segments):
            # Each segment is a speech segment
            segment_duration = segment.duration_seconds
            
            # Check if this segment exceeds the limit
            if segment_duration > max_voiced_without_breath:
                max_voiced_without_breath = segment_duration
            
            # Check gap before this segment (if not first segment)
            if i > 0:
                prev_segment = segments[i - 1]
                gap_start = prev_segment.end_seconds
                gap_end = segment.start_seconds
                gap_duration = gap_end - gap_start
                
                # If gap is long enough to be a breath event
                if gap_duration >= MIN_BREATH_SILENCE_SECONDS:
                    breath_event_count += 1
        
        # Check gap after last segment
        if segments:
            last_segment = segments[-1]
            if last_segment.end_seconds < total_duration:
                gap_duration = total_duration - last_segment.end_seconds
                if gap_duration >= MIN_BREATH_SILENCE_SECONDS:
                    breath_event_count += 1
        
        # Check if we have a violation
        has_violation = max_voiced_without_breath > MAX_VOICED_WITHOUT_BREATH_SECONDS
        
        return {
            "has_violation": has_violation,
            "max_voiced_without_breath": max_voiced_without_breath,
            "breath_event_count": breath_event_count,
        }

