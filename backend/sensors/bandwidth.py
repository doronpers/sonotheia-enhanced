"""
Bandwidth sensor for detecting frequency rolloff patterns.

Analyzes spectral characteristics to identify narrowband audio typical
of telephony or AI-generated content with limited frequency range.
"""

import numpy as np
from scipy.fft import rfft
from .base import BaseSensor, SensorResult
from backend.utils.config import get_threshold

# Constants - can be overridden by config/settings.yaml
SPECTRAL_ROLLOFF_THRESHOLD_HZ = get_threshold("bandwidth", "rolloff_threshold_hz", 4000)
SPECTRAL_ROLLOFF_PERCENT = get_threshold("bandwidth", "rolloff_percent", 0.90)
# When true, narrowband detection contributes to SYNTHETIC verdict
CONTRIBUTE_TO_VERDICT = get_threshold("bandwidth", "contribute_to_verdict", True)


class BandwidthSensor(BaseSensor):
    """
    Bandwidth sensor that detects frequency rolloff patterns.
    
    Analyzes the spectral rolloff frequency to determine if audio is
    narrowband (typical of telephony or some AI systems) or fullband
    (typical of high-quality recordings).
    
    When contribute_to_verdict is True, narrowband detection flags the audio
    as potentially synthetic (passed=False for narrowband, passed=True for fullband).
    When False, it remains info-only (passed=None).
    """
    
    def __init__(
        self,
        rolloff_threshold_hz: int = SPECTRAL_ROLLOFF_THRESHOLD_HZ,
        rolloff_percent: float = SPECTRAL_ROLLOFF_PERCENT,
        contribute_to_verdict: bool = CONTRIBUTE_TO_VERDICT,
        category: str = "defense",
    ):
        """
        Initialize bandwidth sensor.
        
        Args:
            rolloff_threshold_hz: Frequency threshold for narrowband classification (default: 4000Hz)
            rolloff_percent: Percentage of energy to use for rolloff calculation (default: 0.90)
            contribute_to_verdict: If True, narrowband detection contributes to verdict (default: True)
            category: "prosecution" or "defense"
        """
        super().__init__("Bandwidth Sensor (Rolloff Frequency)", category=category)
        self.rolloff_threshold_hz = rolloff_threshold_hz
        self.rolloff_percent = rolloff_percent
        self.contribute_to_verdict = contribute_to_verdict
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for frequency bandwidth characteristics.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with bandwidth classification
        """
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=None,  # Info-only for invalid input
                value=0,
                threshold=self.rolloff_threshold_hz,
                metadata={"type": "UNKNOWN"}
            )
        
        # Use rfft for real audio signals (2x faster than fft)
        # rfft already returns only positive frequencies
        spectrum = np.abs(rfft(audio_data))
        spectral_sum = np.sum(spectrum)
        
        if spectral_sum == 0:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0,
                threshold=self.rolloff_threshold_hz,
                metadata={"type": "SILENCE"}
            )
        
        energy_threshold = spectral_sum * self.rolloff_percent
        cumulative_energy = np.cumsum(spectrum)
        # Optimize search for rolloff index using searchsorted (O(log n) vs O(n))
        # cumulative_energy is sorted by definition
        rolloff_idx = np.searchsorted(cumulative_energy, energy_threshold)
        
        if rolloff_idx >= len(spectrum):
            # Should not happen if logic is correct, but safety check
            rolloff_idx = len(spectrum) - 1
        # For rfft, nyquist frequency corresponds to len(spectrum)
        rolloff_hz = (rolloff_idx / len(spectrum)) * (samplerate / 2)
        is_narrowband = rolloff_hz < self.rolloff_threshold_hz
        bandwidth_type = "NARROWBAND" if is_narrowband else "FULLBAND"
        
        # Determine context (Phone vs HD)
        # Narrowband (<4kHz) = Phone/VoIP context
        # Wideband (>4kHz) = HD/Studio context
        context = "NARROWBAND" if is_narrowband else "WIDEBAND"
        
        # NOTE: BandwidthSensor no longer votes on Real/Fake.
        # It provides CONTEXT for the Fusion Engine to select the correct profile.
        # passed=None ensures it doesn't affect the score.
        passed = None
        detail = f"Context Detected: {context} (Rolloff: {int(rolloff_hz)}Hz)"
        
        result = SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=int(rolloff_hz),
            threshold=self.rolloff_threshold_hz,
            detail=detail,
            metadata={
                "type": bandwidth_type,
                "context": context, 
                "rolloff_hz": int(rolloff_hz)
            }
        )
        
        return result

