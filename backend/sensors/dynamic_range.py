"""
Dynamic range sensor for detecting compression artifacts.

Measures crest factor to identify unnaturally compressed audio typical
of synthetic speech generation systems.
"""

import numpy as np
from .base import BaseSensor, SensorResult
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
    
    def __init__(self, crest_factor_threshold: float = CREST_FACTOR_THRESHOLD):
        """
        Initialize dynamic range sensor.
        
        Args:
            crest_factor_threshold: Minimum acceptable crest factor (default: 5.0 from config)
        """
        super().__init__("Dynamic Range Sensor (Crest Factor)")
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
        
        if not passed:
            result.reason = "SYNTHETIC"
            result.detail = f"Audio is unnaturally compressed (Crest Factor: {round(crest_factor, 2)})."
        
        return result

