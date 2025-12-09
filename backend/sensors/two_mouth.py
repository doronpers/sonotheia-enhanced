"""
Two-Mouth Sensor: Detects Anatomical State Conflicts.

This sensor identifies audio segments where acoustic features imply contradictory 
physiological states, such as simultaneous incompatible articulations or rapid 
changes in vocal tract length (VTL) that suggest multiple speakers or model artifacts.

Key Detection Methods:
1. Vocal Tract Length (VTL) Variance: Rapid shifts in estimated VTL.
2. Spectral Conflict: Simultaneous presence of incompatible spectral cues.
"""

import numpy as np
import logging
from typing import Dict, Tuple
from scipy import signal

from .base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

class TwoMouthSensor(BaseSensor):
    """
    Detects "Two-Mouth" artifacts where acoustic features contradict physical constraints.
    
    Analyzes:
    - VTL Stability: Vocal tract length should be relatively stable for a single speaker.
    - Spectral Consistency: Detects simultaneous incompatible spectral shapes.
    """

    def __init__(self):
        super().__init__("Two-Mouth Sensor")
        
    def analyze(self, audio: np.ndarray, sr: int) -> SensorResult:
        """
        Analyze audio for anatomical state conflicts.
        """
        if not self.validate_input(audio, sr):
             return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )

        try:
            # 1. VTL Variance Analysis
            vtl_score, vtl_details = self._analyze_vtl_variance(audio, sr)
            
            # 2. Spectral Conflict Analysis
            conflict_score, conflict_details = self._analyze_spectral_conflict(audio, sr)
            
            # Combine scores (weighted)
            # VTL variance is a strong indicator of "morphing" voices
            # Spectral conflict indicates "glitching" or multi-speaker artifacts
            combined_score = (vtl_score * 0.6) + (conflict_score * 0.4)
            
            passed = combined_score < 0.5
            
            detail = f"Two-Mouth analysis passed. Score: {combined_score:.2f}"
            if not passed:
                detail = (
                    f"Anatomical state conflicts detected. "
                    f"Score: {combined_score:.2f} (VTL Var: {vtl_score:.2f}, "
                    f"Spectral Conflict: {conflict_score:.2f})"
                )
                
            return SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=round(combined_score, 3),
                threshold=0.5,
                detail=detail,
                metadata={
                    "vtl_score": round(vtl_score, 3),
                    "vtl_variance": vtl_details.get("variance", 0.0),
                    "spectral_conflict_score": round(conflict_score, 3),
                    "conflict_count": conflict_details.get("count", 0)
                }
            )

        except Exception as e:
            logger.error(f"Two-Mouth analysis failed: {e}", exc_info=True)
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                reason="ERROR",
                detail=f"Analysis failed: {str(e)}"
            )

    def _analyze_vtl_variance(self, audio: np.ndarray, sr: int) -> Tuple[float, Dict]:
        """
        Estimate Vocal Tract Length (VTL) over time and check for unnatural variance.
        
        Method:
        - Extract formants (F1, F2, F3, F4)
        - Estimate VTL using F3/F4 (which are more correlated with VTL than F1/F2)
        - VTL = (2n - 1) * c / (4 * Fn)  (Open tube model approximation)
        """
        # Simplified VTL estimation using spectral peaks
        # We look for stability of higher frequency peaks (approx F3/F4 range)
        
        f, t, Sxx = signal.spectrogram(audio, sr, nperseg=1024, noverlap=512)
        
        # Focus on 2500Hz - 4500Hz range (typical F3/F4 for adults)
        freq_mask = (f >= 2500) & (f <= 4500)
        band_energy = Sxx[freq_mask, :]
        
        # Find dominant frequency in this band for each time step
        # This is a rough proxy for a higher formant
        if band_energy.size == 0:
             return 0.0, {"variance": 0.0}

        peak_indices = np.argmax(band_energy, axis=0)
        peak_freqs = f[freq_mask][peak_indices]
        
        # Filter out low energy frames (silence/unvoiced)
        energy_profile = np.sum(Sxx, axis=0)
        threshold = np.percentile(energy_profile, 20)
        voiced_mask = energy_profile > threshold
        
        if np.sum(voiced_mask) < 10:
            return 0.0, {"variance": 0.0}
            
        voiced_peaks = peak_freqs[voiced_mask]
        
        # Calculate variance of these peaks
        # High variance suggests the "tube length" is changing rapidly
        # Normalize by mean to get coefficient of variation
        mean_freq = np.mean(voiced_peaks)
        if mean_freq == 0:
            return 0.0, {"variance": 0.0}
            
        cv = np.std(voiced_peaks) / mean_freq
        
        # Thresholds
        # Natural speech has some VTL variation due to lip rounding/larynx height,
        # but it shouldn't be extreme.
        # CV > 0.15 is suspicious for a short segment
        
        score = min(1.0, max(0.0, (cv - 0.10) * 10)) # 0.10 -> 0.0, 0.20 -> 1.0
        
        return score, {"variance": float(cv)}

    def _analyze_spectral_conflict(self, audio: np.ndarray, sr: int) -> Tuple[float, Dict]:
        """
        Detect simultaneous incompatible spectral cues.
        
        Example: Strong low-frequency energy (voicing) AND strong high-frequency 
        noise (frication) WITHOUT the expected formant structure connecting them.
        This often happens in "glitchy" samples.
        """
        # Compute spectral flatness (tonality) in bands
        # Low band: 100-1000 Hz
        # High band: 4000-8000 Hz
        
        S = np.abs(librosa.stft(audio, n_fft=2048, hop_length=512)) if 'librosa' in globals() else None
        
        # Fallback if librosa not available or for simplicity in this draft
        # We'll use scipy for a basic check
        f, t, Sxx = signal.spectrogram(audio, sr, nperseg=1024)
        
        low_mask = (f >= 100) & (f <= 1000)
        high_mask = (f >= 4000) & (f <= 8000)
        
        low_energy = np.sum(Sxx[low_mask, :], axis=0)
        high_energy = np.sum(Sxx[high_mask, :], axis=0)
        
        # Normalize
        low_energy = low_energy / (np.max(low_energy) + 1e-6)
        high_energy = high_energy / (np.max(high_energy) + 1e-6)
        
        # Detect frames where BOTH are very high
        # In natural speech, voiced fricatives (z, v) have this, but usually 
        # with specific ratios. Deepfakes can have "full volume" in both bands.
        conflict_mask = (low_energy > 0.8) & (high_energy > 0.8)
        conflict_count = np.sum(conflict_mask)
        
        conflict_rate = conflict_count / len(low_energy)
        
        # Threshold
        # > 5% of frames having max energy in both bands is suspicious
        score = min(1.0, max(0.0, (conflict_rate - 0.05) * 10))
        
        return score, {"count": int(conflict_count)}
