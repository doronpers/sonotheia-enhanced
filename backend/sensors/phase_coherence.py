"""
Phase Coherence Sensor - Patent-Safe Vocoder Artifact Detection

**Patent Compliance**: This implementation uses PHASE-PHYSICS MODEL
(phase derivative entropy) rather than LPC residuals or source-filter modeling,
providing freedom to operate around Pindrop's patents.

**Design-Around Strategy**:
- ❌ RESTRICTED: LPC residuals, glottal closure/opening analysis
- ✅ SAFE: Phase derivative entropy, instantaneous frequency analysis

Detects synthetic speech by identifying vocoder artifacts through 
phase discontinuities and unnatural phase coherence patterns.
"""

import numpy as np
from scipy import signal
from scipy.stats import entropy
from typing import Dict, Any, Optional
import logging

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)


class PhaseCoherenceSensor(BaseSensor):
    """
    Analyzes phase coherence using instantaneous frequency entropy.
    
    **Patent-Safe Approach**:
    - Uses Hilbert transform for analytic signal
    - Calculates instantaneous frequency (phase derivative)  
    - Measures Shannon entropy of phase derivative distribution
    - Detects vocoder artifacts via phase discontinuities
    - No LPC, no residuals, no source-filter modeling
    
    Synthetic speech from vocoders often exhibits:
    - Lower entropy (too regular/predictable phase)
    - Abrupt phase resets ("digital silence")
    - Unnatural phase coherence across frequency bands
    """
    
    def __init__(self):
        super().__init__()
        self.name = "PhaseCoherence"
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze phase coherence using entropy of instantaneous frequency.
        
        Args:
            audio_data: Audio signal (normalized float32)
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult indicating if phase patterns are natural
        """
        try:
            # Calculate instantaneous phase using Hilbert transform
            analytic_signal = signal.hilbert(audio_data)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal))
            
            # Calculate instantaneous frequency (phase derivative)
            # This is the core "phase-physics" measurement
            instantaneous_freq = np.diff(instantaneous_phase) * samplerate / (2 * np.pi)
            
            # Remove outliers (due to numerical issues at silence)
            instantaneous_freq = self._remove_outliers(instantaneous_freq)
            
            if len(instantaneous_freq) == 0:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.0,
                    threshold=0.0,
                    reason="Insufficient data for phase analysis",
                    detail="Audio too short or all silence"
                )
            
            # Calculate Shannon entropy of instantaneous frequency distribution
            # High entropy = natural (unpredictable phase evolution)
            # Low entropy = synthetic (too regular, vocoder artifact)
            phase_entropy = self._calculate_phase_entropy(instantaneous_freq)
            
            # Detect "digital silence" artifacts (abrupt phase resets)
            num_discontinuities = self._detect_phase_discontinuities(instantaneous_phase)
            
            # Calculate coherence score
            # High entropy is good (natural), low is suspicious
            # Normalize entropy to 0-1 range (empirically, natural speech ~3-6 nats)
            normalized_entropy = min(phase_entropy / 6.0, 1.0)
            
            # Penalize for discontinuities
            discontinuity_penalty = min(num_discontinuities * 0.05, 0.3)
            coherence_score = max(normalized_entropy - discontinuity_penalty, 0.0)
            
            # Threshold: coherence score < 0.4 indicates synthetic
            threshold = 0.4
            passed = coherence_score >= threshold
            
            detail_parts = [
                f"Entropy: {phase_entropy:.3f}",
                f"Coherence: {coherence_score:.3f}"
            ]
            
            if num_discontinuities > 0:
                detail_parts.append(f"Discontinuities: {num_discontinuities}")
            
            return SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=float(coherence_score),
                threshold=threshold,
                reason="Low phase coherence (vocoder artifacts)" if not passed else None,
                detail=", ".join(detail_parts),
                metadata={
                    "phase_entropy_nats": float(phase_entropy),
                    "discontinuities": int(num_discontinuities),
                    "mean_inst_freq": float(np.mean(instantaneous_freq))
                }
            )
            
        except Exception as e:
            logger.error(f"Phase coherence analysis failed: {e}", exc_info=True)
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.0,
                reason=f"Analysis failed: {str(e)}",
                detail=None
            )
    
    def _remove_outliers(self, data: np.ndarray, threshold: float = 3.0) -> np.ndarray:
        """
        Remove outliers using Z-score method.
        
        Args:
            data: Input array
            threshold: Z-score threshold (standard deviations)
            
        Returns:
            Data with outliers removed
        """
        if len(data) == 0:
            return data
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return data
        
        z_scores = np.abs((data - mean) / std)
        return data[z_scores < threshold]
    
    def _calculate_phase_entropy(self, instantaneous_freq: np.ndarray) -> float:
        """
        Calculate Shannon entropy of instantaneous frequency distribution.
        
        **Patent-Safe**: Analyzes phase derivative distribution, not LPC residuals.
        
        Args:
            instantaneous_freq: Instantaneous frequency values
            
        Returns:
            Shannon entropy in nats (natural logarithm)
        """
        # Create histogram of instantaneous frequencies
        # More bins = more sensitive to regularity
        hist, bin_edges = np.histogram(instantaneous_freq, bins=50, density=True)
        
        # Normalize to probability distribution
        hist = hist / np.sum(hist)
        
        # Remove zero bins (log(0) is undefined)
        hist = hist[hist > 0]
        
        # Calculate Shannon entropy: -sum(p * log(p))
        phase_entropy = entropy(hist, base=np.e)  # Use natural log (nats)
        
        return phase_entropy
    
    def _detect_phase_discontinuities(
        self, 
        instantaneous_phase: np.ndarray,
        threshold_std: float = 10.0
    ) -> int:
        """
        Detect abrupt phase resets ("digital silence" artifacts).
        
        Vocoder artifacts often manifest as sudden phase jumps when
        transitioning between synthetic segments.
        
        Args:
            instantaneous_phase: Unwrapped instantaneous phase
            threshold_std: Threshold in standard deviations
            
        Returns:
            Number of discontinuities detected
        """
        # Calculate second derivative (acceleration of phase)
        phase_accel = np.diff(instantaneous_phase, n=2)
        
        if len(phase_accel) == 0:
            return 0
        
        # Find points where acceleration is abnormally high
        mean_accel = np.mean(phase_accel)
        std_accel = np.std(phase_accel)
        
        if std_accel == 0:
            return 0
        
        # Count discontinuities (phase accelerations > threshold)
        z_scores = np.abs((phase_accel - mean_accel) / std_accel)
        num_discontinuities = np.sum(z_scores > threshold_std)
        
        return int(num_discontinuities)
