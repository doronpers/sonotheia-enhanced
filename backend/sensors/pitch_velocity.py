"""
Pitch Velocity Sensor.

Detects "Super-Human" pitch glides that violate laryngeal muscle constraints.
Neural vocoders often generate pitch contours that are mathematically smooth
but physically impossible for a biological larynx to execute.

Key Metric: Pitch Velocity (Semitones per Second)
"""

import numpy as np
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from .base import BaseSensor, SensorResult
from backend.utils.config import get_threshold

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

logger = logging.getLogger(__name__)

@dataclass
class PitchVelocityConfig:
    max_velocity_threshold: float = 35.0  # Max humanly possible st/s (Conservative)
    min_voiced_duration: float = 0.05     # Min duration to consider a glide
    hop_length_ms: float = 10.0           # Analysis resolution

class PitchVelocitySensor(BaseSensor):
    """
    Detects impossible laryngeal movements (Pitch Velocity).
    
    Physics:
    The cricothyroid muscle controls vocal fold tension (pitch).
    It has a maximum contraction speed. Transitions faster than
    this biological limit indicate synthetic generation.
    """
    
    def __init__(self, config: Optional[PitchVelocityConfig] = None, category: str = "prosecution"):
        super().__init__("Pitch Velocity Sensor (Larynx Analysis)", category=category)
        self.config = config or PitchVelocityConfig()

    def analyze(self, audio: np.ndarray, sr: int) -> SensorResult:
        if not HAS_LIBROSA:
             return SensorResult(self.name, None, 0.0, 0.0, detail="Librosa missing")
             
        if not self.validate_input(audio, sr):
             return SensorResult(self.name, None, 0.0, 0.0, detail="Invalid input")

        # 1. Extract Pitch (F0)
        # using pyin for robustness (probabilistic YIN)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
            frame_length=2048,
            hop_length=int(self.config.hop_length_ms * sr / 1000)
        )
        
        # 2. Compute Velocity (Semitones per Second)
        velocity_stats = self._compute_pitch_velocity(f0, voiced_flag, sr)
        
        max_vel = velocity_stats['max_velocity']
        avg_vel = velocity_stats['avg_velocity']
        
        # 3. Verdict
        # If we see sustained "super-human" glides
        is_suspicious = max_vel > self.config.max_velocity_threshold
        
        # Use a soft score based on how far past the limit it went
        # Sigmoid-like mapping
        # 35 st/s -> 0.5
        # 70 st/s -> 1.0
        score = min(1.0, max(0.0, (max_vel - 20) / 40)) 
        
        passed = score < 0.5
        
        detail = f"Max Glide: {max_vel:.1f} st/s (Limit: {self.config.max_velocity_threshold})."
        if not passed:
            detail = f"Impossible Laryngeal Velocity: {max_vel:.1f} st/s detected. " \
                     f"Exceeds biological limit ({self.config.max_velocity_threshold} st/s)."

        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=score,
            threshold=0.5,
            detail=detail,
            metadata={
                "max_velocity_st_s": float(max_vel),
                "avg_velocity_st_s": float(avg_vel),
                "voiced_percent": float(np.mean(voiced_flag))
            }
        )

    def _compute_pitch_velocity(self, f0: np.ndarray, voiced: np.ndarray, sr: int) -> Dict[str, float]:
        """Compute the first derivative of pitch in semitones per second."""
        if np.sum(voiced) < 5: # Not enough speech
            return {'max_velocity': 0.0, 'avg_velocity': 0.0}
            
        # Convert Hz to Semitones (relative to C2 approx 65Hz)
        # Only for voiced segments
        f0_clean = np.where(voiced, f0, np.nan)
        
        # Log scale (semitones)
        # 12 * log2(f1/f2)
        # derivative = 12 * log2(f[t+1]/f[t]) / dt
        
        # Calculate frame time delta
        dt = self.config.hop_length_ms / 1000.0
        
        # Calculate velocity frame-by-frame
        velocities = []
        
        for i in range(len(f0_clean) - 1):
            if voiced[i] and voiced[i+1]:
                if f0_clean[i] > 0 and f0_clean[i+1] > 0:
                    # Pitch change in semitones
                    st_change = 12 * np.log2(f0_clean[i+1] / f0_clean[i])
                    vel = abs(st_change) / dt
                    velocities.append(vel)
        
        if not velocities:
            return {'max_velocity': 0.0, 'avg_velocity': 0.0}
            
        vel_array = np.array(velocities)
        
        # Use 99th percentile to filter single-frame outliers/tracking errors
        max_v = np.percentile(vel_array, 99)
        avg_v = np.mean(vel_array)
        
        return {
            'max_velocity': max_v,
            'avg_velocity': avg_v
        }
