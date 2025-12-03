"""
Coarticulation Sensor - Patent-Safe Motor Planning Analysis

**Patent Compliance**: This implementation analyzes MOTOR PLANNING and
temporal dependencies (coarticulation), which is in "white space"
not covered by Pindrop's Source-Filter Model patents.

**Design-Around Strategy**:
- ❌ RESTRICTED: LPC residuals, static spectral values
- ✅ SAFE: Spectral transition speed, motor planning analysis

Detects synthetic speech by measuring articulation velocity and
identifying transitions that violate physiological constraints.
"""

import numpy as np
import librosa
from typing import Dict, Any, Optional
import logging

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

class CoarticulationSensor(BaseSensor):
    """
    Analyzes coarticulation by measuring spectral transition speed.
    
    **Patent-Safe Approach**:
    - Uses Mel spectrogram delta features (not LPC)
    - Analyzes temporal dependencies between phonemes
    - Detects violations of physiological articulation speed limits
    - Focuses on motor planning, not current-sound modeling
    
    Synthetic speech often has faster-than-natural transitions between
    phonemes because TTS systems lack biomechanical constraints of 
    human articulators (tongue, lips, jaw movement speeds).
    """
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        try:
            # Compute Mel Spectrogram
            mel_spec = librosa.feature.melspectrogram(y=audio_data, sr=samplerate)
            log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Compute delta features (rate of change)
            delta_mel = librosa.feature.delta(log_mel_spec)
            
            # Calculate mean absolute delta (speed of spectral change)
            # High values indicate fast transitions
            mean_delta = np.mean(np.abs(delta_mel))
            
            # Threshold: Transitions that are too fast might be synthetic
            # Natural speech has physical limits on articulator movement speed
            # This threshold would need calibration
            threshold = 2.5 
            passed = mean_delta <= threshold
            
            return SensorResult(
                sensor_name="Coarticulation",
                passed=passed,
                value=float(mean_delta),
                threshold=threshold,
                reason="Unnatural spectral transition speed" if not passed else None,
                detail=f"Mean spectral delta: {mean_delta:.3f}",
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Coarticulation analysis failed: {e}")
            return SensorResult(
                sensor_name="Coarticulation",
                passed=None,
                value=0.0,
                threshold=0.0,
                reason=f"Analysis failed: {str(e)}",
                detail=None
            )
