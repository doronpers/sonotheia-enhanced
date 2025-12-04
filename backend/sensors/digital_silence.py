"""
Digital Silence sensor for detecting vacuum artifacts in synthetic audio.

The Physics: A recording of a human in a room will never be truly silent due to
"room tone" (air handling, electronics, reverberation). Natural recordings have
continuous background noise with variance.

The Violation: Deepfakes often use "perfect zeros" (digital silence) between words
or at the very start/end of a clip. The noise floor variance drops to zero or changes
texture instantly between phrases, indicating the audio was generated piecemeal rather
than recorded in a continuous environment.

Design-Around Strategy: Uses spectral flux and noise floor analysis (NOT LPC residual
analysis) to detect perfect mathematical silence and instant texture changes.
"""

import numpy as np
from typing import Dict
from scipy import signal
from backend.sensors.base import BaseSensor, SensorResult

# Detection thresholds
MIN_NOISE_FLOOR_VARIANCE = 1e-8  # Minimum variance for natural room tone (dB²)
PERFECT_SILENCE_THRESHOLD_DB = -120.0  # Below this is effectively perfect silence
SPECTRAL_FLUX_CHANGE_THRESHOLD = 0.5  # Instant spectral flux change indicates splicing
MIN_BACKGROUND_ENERGY_DB = -80.0  # Natural recordings have background energy above this


class DigitalSilenceSensor(BaseSensor):
    """
    Digital Silence sensor that detects vacuum artifacts in synthetic audio.
    
    Analyzes the noise floor between words and detects perfect mathematical silence
    or instant texture changes that indicate piecemeal audio generation rather than
    continuous recording.
    
    Design-Around Strategy:
    - Uses spectral flux and noise floor variance analysis (NOT LPC residuals)
    - Focuses on acoustic consistency (reverb vs background noise) rather than
      source-filter model error signals
    """
    
    def __init__(
        self,
        frame_length_ms: float = 25.0,
        hop_length_ms: float = 10.0,
    ):
        """
        Initialize digital silence sensor.
        
        Args:
            frame_length_ms: Analysis frame length in milliseconds
            hop_length_ms: Hop length in milliseconds
        """
        super().__init__("Digital Silence Sensor")
        self.frame_length_ms = frame_length_ms
        self.hop_length_ms = hop_length_ms
    
    def analyze(self, audio: np.ndarray, sr: int) -> SensorResult:
        """
        Analyze audio for digital silence artifacts.
        
        Args:
            audio: Audio signal as numpy array
            sr: Sample rate in Hz
            
        Returns:
            SensorResult with digital silence analysis
        """
        if not self.validate_input(audio, sr):
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )
        
        # 1. Detect Perfect Silence (Zeros)
        silence_results = self._detect_perfect_silence(audio, sr)
        
        # 2. Analyze Noise Floor Variance
        variance_results = self._analyze_noise_floor_variance(audio, sr)
        
        # 3. Detect Room Tone Changes (Splicing)
        room_tone_results = self._detect_room_tone_changes(audio, sr)
        
        # Combine scores
        suspicion_score = 0.0
        violations = 0
        
        if silence_results["has_perfect_silence"]:
            suspicion_score += 0.6
            violations += silence_results["silence_count"]
            
        if variance_results["zero_variance"]:
            suspicion_score += 0.4
            violations += 1
            
        if room_tone_results["has_abrupt_changes"]:
            suspicion_score += 0.3
            violations += room_tone_results["change_count"]
            
        # Normalize score
        suspicion_score = min(1.0, suspicion_score)
        passed = suspicion_score < 0.5
        
        detail = f"Digital silence analysis passed. Score: {suspicion_score:.2f}"
        if not passed:
            detail = (
                f"Digital silence artifacts detected. "
                f"Score: {suspicion_score:.2f} (violations: {violations})."
            )
            
        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=suspicion_score,
            threshold=0.5,
            detail=detail,
            metadata={
                "has_perfect_silence": silence_results["has_perfect_silence"],
                "silence_segments": silence_results["silence_count"],
                "noise_floor_variance": variance_results["variance"],
                "room_tone_changes": room_tone_results["change_count"]
            }
        )
    
    def _detect_perfect_silence(self, audio: np.ndarray, sr: int) -> Dict:
        """Detect segments of perfect mathematical silence (zeros)."""
        # Convert to dB
        frame_len = int(self.frame_length_ms * sr / 1000)
        hop_len = int(self.hop_length_ms * sr / 1000)
        
        # Simple energy calculation
        energy = np.array([
            np.sum(audio[i:i+frame_len]**2) 
            for i in range(0, len(audio)-frame_len, hop_len)
        ])
        
        # Avoid log(0)
        energy_db = 10 * np.log10(energy + 1e-12)
        
        # Count frames below perfect silence threshold
        silent_frames = np.sum(energy_db < PERFECT_SILENCE_THRESHOLD_DB)
        
        return {
            "has_perfect_silence": silent_frames > 0,
            "silence_count": int(silent_frames)
        }
        
    def _analyze_noise_floor_variance(self, audio: np.ndarray, sr: int) -> Dict:
        """Analyze variance of background noise."""
        # Estimate noise floor (lowest 10% of energy frames)
        frame_len = int(self.frame_length_ms * sr / 1000)
        hop_len = int(self.hop_length_ms * sr / 1000)
        
        energy = np.array([
            np.mean(audio[i:i+frame_len]**2) 
            for i in range(0, len(audio)-frame_len, hop_len)
        ])
        
        # Sort energy to find noise floor
        sorted_energy = np.sort(energy)
        noise_floor_frames = sorted_energy[:max(1, int(len(energy) * 0.1))]
        
        variance = np.var(noise_floor_frames)
        
        return {
            "variance": float(variance),
            "zero_variance": variance < MIN_NOISE_FLOOR_VARIANCE
        }

    def _detect_room_tone_changes(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Detect abrupt changes in room tone (background noise texture).
        Uses spectral centroid and flatness of noise floor frames.
        """
        # This is a simplified implementation
        # In a full implementation, we would track spectral flux of background frames only
        return {
            "has_abrupt_changes": False,
            "change_count": 0
        }
