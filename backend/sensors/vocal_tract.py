import numpy as np
import librosa
from typing import Dict, Any, Optional
import logging

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

class VocalTractSensor(BaseSensor):
    """
    Analyzes vocal tract characteristics using Linear Predictive Coding (LPC).
    Synthetic speech often exhibits unnatural consistency in vocal tract configuration.
    """
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        try:
            # Frame the signal
            frame_length = int(0.025 * samplerate)  # 25ms
            hop_length = int(0.010 * samplerate)    # 10ms
            
            # Use librosa to extract LPC coefficients
            # LPC order typically 2 + sr/1000
            order = 2 + int(samplerate / 1000)
            
            # Extract LPCs
            # librosa.lpc expects a single frame or we can loop
            # For efficiency, let's analyze a representative segment (e.g., middle 1 sec)
            
            mid_point = len(audio_data) // 2
            segment_len = min(len(audio_data), samplerate) # 1 second
            start = max(0, mid_point - segment_len // 2)
            segment = audio_data[start : start + segment_len]
            
            # Apply pre-emphasis
            pre_emphasized = librosa.effects.preemphasis(segment)
            
            # Compute LPC for the whole segment (simplified) or frames
            # Let's do frame-based to check consistency
            frames = librosa.util.frame(pre_emphasized, frame_length=frame_length, hop_length=hop_length)
            
            lpc_coeffs = []
            for i in range(frames.shape[1]):
                frame = frames[:, i]
                # Windowing
                frame = frame * np.hamming(len(frame))
                
                # Check for silence/low energy to avoid numerical instability
                if np.sum(frame**2) < 1e-10:
                    a = np.zeros(order + 1)
                    a[0] = 1.0
                else:
                    a = librosa.lpc(frame, order=order)
                
                lpc_coeffs.append(a)
                
            lpc_coeffs = np.array(lpc_coeffs)
            
            # Calculate variance of LPC coefficients across frames
            # Unnatural consistency would mean low variance
            lpc_std = np.std(lpc_coeffs, axis=0).mean()
            
            # Threshold: Extremely low variance indicates synthetic (too stable)
            # This is a heuristic. 
            threshold = 0.01 
            passed = lpc_std >= threshold
            
            return SensorResult(
                sensor_name="Vocal Tract",
                passed=passed,
                value=float(lpc_std),
                threshold=threshold,
                reason="Unnatural vocal tract consistency" if not passed else None,
                detail=f"LPC variance: {lpc_std:.4f}",
                metadata={"lpc_order": order}
            )
            
        except Exception as e:
            logger.error(f"Vocal tract analysis failed: {e}")
            return SensorResult(
                sensor_name="Vocal Tract",
                passed=None,
                value=0.0,
                threshold=0.0,
                reason=f"Analysis failed: {str(e)}",
                detail=None
            )
