"""
Dynamic range sensor for detecting compression artifacts.

Measures crest factor to identify unnaturally compressed audio typical
of synthetic speech generation systems.
"""

import numpy as np
from .base import BaseSensor, SensorResult
from backend.calibration.environment import EnvironmentAnalyzer
from backend.utils.config import get_threshold

# Default constant - can be overridden by config/settings.yaml
# Lowered from 12.0 to 5.0 to reduce false positives on normal speech
CREST_FACTOR_THRESHOLD = get_threshold("dynamic_range", "crest_factor_threshold", 5.0)


class DynamicRangeSensor(BaseSensor):
    """
    Dynamic range sensor that detects compression artifacts.
    
    Measures the crest factor (peak-to-RMS ratio) of audio. Real speech
    has natural dynamic range with high crest factors. Synthetic audio
    often shows unnaturally low crest factors due to compression artifacts.
    """
    
    def __init__(self, crest_factor_threshold: float = CREST_FACTOR_THRESHOLD, category: str = "defense"):
        """
        Initialize dynamic range sensor.
        
        Args:
            crest_factor_threshold: Minimum acceptable crest factor (default: 5.0 from config)
            category: "prosecution" or "defense"
        """
        super().__init__("Dynamic Range Sensor (Crest Factor)", category=category)
        self.crest_factor_threshold = crest_factor_threshold
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for dynamic range compression.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz (unused but kept for API consistency)
            
        Returns:
            SensorResult with crest factor analysis
        """
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=0.0,
                threshold=self.crest_factor_threshold,
                detail="Invalid or empty audio input."
            )
        
        peak_amplitude = np.max(np.abs(audio_data))
        rms_amplitude = np.sqrt(np.mean(np.square(audio_data)))
        
        # Dynamic Calibration: Adapt threshold based on SNR
        env_stats = EnvironmentAnalyzer.analyze(audio_data, samplerate)
        snr_db = env_stats["snr_db"]
        
        # Base threshold from config/class
        adapted_threshold = self.crest_factor_threshold
        
        # If SNR is low (< 15dB), the audio is noisy/compressed, which naturally lowers crest factor.
        # We should relax the threshold to avoid false positives on bad lines.
        if snr_db < 15.0:
            # Linearly relax threshold as SNR drops from 15dB to 5dB
            # At 15dB -> factor 1.0
            # At 5dB  -> factor 0.6
            reduction_factor = max(0.6, 0.6 + (0.4 * (snr_db - 5.0) / 10.0))
            adapted_threshold *= reduction_factor
            # logger.debug(f"DynamicRange: Lowered threshold to {adapted_threshold:.2f} due to low SNR ({snr_db:.1f}dB)")
        
        if rms_amplitude == 0:
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=-1.0,
                threshold=self.crest_factor_threshold,
                detail="Pure silence."
            )
        
        crest_factor = peak_amplitude / rms_amplitude
        passed = bool(crest_factor > self.crest_factor_threshold)
        
        result = SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=round(crest_factor, 2),
            threshold=self.crest_factor_threshold,
        )
        
        # Calculate normalized anomaly score (0.0 = Real, 1.0 = Fake)
        # Dynamic Range is a "Higher is Better" metric (Crest Factor).
        # We need to invert it for anomaly scoring.
        # If CF is 2.0 (Bad), Score -> 1.0
        # If CF is 10.0 (Good), Score -> 0.0
        # Threshold is ~5.0
        
        # Map: 0.0 -> 1.0 (Worst), Threshold -> 0.5, Threshold*2 -> 0.0
        if crest_factor >= self.crest_factor_threshold * 2:
            normalized_score = 0.0
        elif crest_factor <= 0:
            normalized_score = 1.0
        else:
             # Linear interpolation between 0 and Threshold*2
             # Normalized x: 0..10
             # Inverted: 1 - (x / 10)
             max_healthy = self.crest_factor_threshold * 2
             normalized_score = 1.0 - (crest_factor / max_healthy)
             
        # Clamp
        normalized_score = float(max(0.0, min(1.0, normalized_score)))
        
        result.score = normalized_score
        
        if not passed:
            result.reason = "SYNTHETIC"
            result.detail = f"Audio is unnaturally compressed (Crest Factor: {round(crest_factor, 2)})."
        
        return result

