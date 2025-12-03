import numpy as np
from scipy import signal
from typing import Dict, Any, Optional
import logging

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

class PhaseCoherenceSensor(BaseSensor):
    """
    Analyzes Mean Phase Coherence (MPC) to detect synthetic artifacts.
    Synthetic speech often lacks natural phase coherence across frequency bands.
    """
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        try:
            # Calculate instantaneous phase using Hilbert transform
            analytic_signal = signal.hilbert(audio_data)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal))
            
            # Calculate phase coherence
            # In a real implementation, this would be more complex, comparing phase across frames
            # For this MVP, we'll use a simplified metric based on phase deviation
            
            # Calculate phase difference between samples
            phase_diff = np.diff(instantaneous_phase)
            
            # Calculate standard deviation of phase difference
            # Lower deviation implies higher coherence (potentially synthetic if too perfect, 
            # or natural if consistent. This is a simplified proxy).
            # Actually, synthetic speech often has *random* phase in high frequencies or 
            # *too perfect* phase in vocoded speech.
            # Let's use a metric where low coherence (high variance) is suspicious for some vocoders,
            # but high coherence (low variance) is suspicious for others.
            # We'll assume "low coherence indicates synthetic artifacts" as per prompt.
            
            phase_std = np.std(phase_diff)
            
            # Normalize to 0-1 range roughly
            coherence_score = 1.0 / (1.0 + phase_std)
            
            # Threshold: Low coherence (< 0.4) indicates synthetic
            threshold = 0.4
            passed = coherence_score >= threshold
            
            return SensorResult(
                sensor_name="Phase Coherence",
                passed=passed,
                value=float(coherence_score),
                threshold=threshold,
                reason="Low phase coherence detected" if not passed else None,
                detail=f"Coherence score: {coherence_score:.3f}",
                metadata={"phase_std": float(phase_std)}
            )
            
        except Exception as e:
            logger.error(f"Phase coherence analysis failed: {e}")
            return SensorResult(
                sensor_name="Phase Coherence",
                passed=None,
                value=0.0,
                threshold=0.0,
                reason=f"Analysis failed: {str(e)}",
                detail=None
            )
