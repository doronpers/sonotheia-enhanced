"""
Phase coherence sensor for detecting vocoder artifacts.

Adapted from RecApp's phase_coherence.py to work with BaseSensor interface.
Detects phase relationship violations that indicate synthetic audio generation.

Key Design-Around Strategy:
- Uses "Phase Entropy" and "Phase Derivative" analysis.
- REMOVED: Glottal Inertia logic (moved to glottal_inertia.py).
- REMOVED: Linear Predictive Coding error signal analysis.
- Focuses on the chaotic nature of natural phase vs. the structured phase of vocoders.
"""

import numpy as np
from scipy import signal
from typing import Dict
from .base import BaseSensor, SensorResult

# Detection thresholds
PLV_NATURAL_MIN = 0.7  # Minimum phase locking value for natural speech
PLV_SYNTHETIC_MAX = 0.5  # Maximum PLV for synthetic speech
PHASE_JUMP_RATE_THRESHOLD = 0.15  # Max acceptable phase discontinuity rate
LOW_FREQ_ENERGY_MIN = 0.6  # Natural speech has 60%+ energy below 4kHz
PARSEVAL_TOLERANCE = 0.01  # Energy conservation tolerance

# Entropy thresholds
PHASE_ENTROPY_MIN = 3.5 # Natural speech usually has high phase entropy
PHASE_ENTROPY_MAX_SYNTHETIC = 2.5 # Vocoders often have lower entropy

# Suspicion score weights
PHASE_JUMP_WEIGHT = 0.3
ENERGY_VIOLATION_WEIGHT = 0.2
ENTROPY_WEIGHT = 0.5


class PhaseCoherenceSensor(BaseSensor):
    """
    Phase coherence sensor that detects vocoder phase artifacts.
    
    Analyzes phase relationships between frequency components to identify
    synthesis patterns. Natural speech has strong phase locking between
    harmonics, while synthetic speech often shows independent synthesis or
    unnatural phase structure (too regular or too random in wrong ways).
    """
    
    def __init__(
        self,
        n_fft: int = 2048,
        hop_length: int = 512,
    ):
        """
        Initialize phase coherence sensor.
        
        Args:
            n_fft: FFT window size
            hop_length: Hop length for STFT
        """
        super().__init__("Phase Coherence Sensor")
        self.n_fft = n_fft
        self.hop_length = hop_length
    
    def analyze(self, audio: np.ndarray, sr: int) -> SensorResult:
        """
        Analyze phase coherence of audio signal.
        
        Args:
            audio: Audio signal as numpy array
            sr: Sample rate in Hz
            
        Returns:
            SensorResult with phase coherence analysis
        """
        if not self.validate_input(audio, sr):
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )
        
        # 1. Analyze Phase Entropy (New Patent-Safe Method)
        entropy_results = self._analyze_phase_entropy(audio, sr)
        
        # 2. Analyze Phase Jumps (Discontinuities)
        jump_results = self._analyze_phase_jumps(audio, sr)
        
        # 3. Analyze Energy Distribution
        energy_results = self._analyze_energy_distribution(audio, sr)
        
        # Combine scores
        suspicion_score = 0.0
        violations = 0
        
        # Entropy check
        if entropy_results["entropy_suspicious"]:
            suspicion_score += ENTROPY_WEIGHT
            violations += 1
            
        # Phase jump check
        if jump_results["jump_rate"] > PHASE_JUMP_RATE_THRESHOLD:
            suspicion_score += PHASE_JUMP_WEIGHT
            violations += 1
            
        # Energy check
        if not energy_results["natural_energy_dist"]:
            suspicion_score += ENERGY_VIOLATION_WEIGHT
            violations += 1
            
        # Normalize score
        suspicion_score = min(1.0, suspicion_score)
        
        passed = suspicion_score < 0.5
        
        detail = f"Phase coherence analysis passed. Score: {suspicion_score:.2f}"
        if not passed:
            detail = (
                f"Phase coherence analysis indicates synthetic audio. "
                f"Score: {suspicion_score:.2f} (violations: {violations}, "
                f"jump rate: {jump_results['jump_rate']:.3f}, "
                f"entropy: {entropy_results['phase_entropy']:.2f})"
            )
        
        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=suspicion_score,
            threshold=0.5,
            detail=detail,
            metadata={
                "violation_count": violations,
                "phase_jump_rate": round(jump_results["jump_rate"], 4),
                "energy_ratio": round(energy_results["low_freq_ratio"], 4),
                "low_freq_ratio": round(energy_results["low_freq_ratio"], 4),
                "phase_entropy": round(entropy_results["phase_entropy"], 4),
                "entropy_suspicious": entropy_results["entropy_suspicious"]
            }
        )
    
    def _analyze_phase_entropy(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Analyze the entropy of the phase derivative.
        Natural speech has high entropy in phase derivatives due to turbulent airflow.
        Vocoders often produce signals with lower, more structured phase entropy.
        """
        # Compute STFT
        f, t, Zxx = signal.stft(audio, fs=sr, nperseg=self.n_fft, noverlap=self.n_fft-self.hop_length)
        
        # Extract phase
        phase = np.angle(Zxx)
        
        # Compute phase derivative (instantaneous frequency deviation)
        # Unwrap phase first to avoid 2pi jumps
        unwrapped_phase = np.unwrap(phase, axis=1)
        phase_derivative = np.diff(unwrapped_phase, axis=1)
        
        # Compute entropy of the distribution of phase derivatives
        # We use a histogram to estimate the probability distribution
        hist, _ = np.histogram(phase_derivative.flatten(), bins=100, density=True)
        
        # Filter zeros to avoid log(0)
        hist = hist[hist > 0]
        
        # Shannon entropy
        entropy = -np.sum(hist * np.log(hist))
        
        # Check if entropy is suspiciously low (characteristic of some vocoders)
        # Note: This threshold might need tuning based on the specific vocoder types
        is_suspicious = entropy < PHASE_ENTROPY_MAX_SYNTHETIC
        
        return {
            "phase_entropy": float(entropy),
            "entropy_suspicious": is_suspicious
        }

    def _analyze_phase_jumps(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Analyze phase discontinuities (jumps) in the signal.
        """
        # Compute analytic signal using Hilbert transform
        analytic_signal = signal.hilbert(audio)
        instantaneous_phase = np.unwrap(np.angle(analytic_signal))
        
        # Compute second derivative of phase (angular acceleration)
        # Large spikes indicate unnatural discontinuities
        phase_accel = np.diff(np.diff(instantaneous_phase))
        
        # Count significant jumps (> pi/2)
        jumps = np.sum(np.abs(phase_accel) > np.pi / 2)
        jump_rate = jumps / (len(audio) / sr)  # Jumps per second
        
        return {
            "jump_count": int(jumps),
            "jump_rate": float(jump_rate)
        }
    
    def _analyze_energy_distribution(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Analyze spectral energy distribution.
        """
        # Compute PSD
        freqs, psd = signal.welch(audio, sr, nperseg=self.n_fft)
        
        # Calculate energy in low (<4kHz) vs high frequencies
        low_mask = freqs < 4000
        total_energy = np.sum(psd)
        
        if total_energy == 0:
            return {"low_freq_ratio": 0.0, "natural_energy_dist": False}
            
        low_energy = np.sum(psd[low_mask])
        low_freq_ratio = low_energy / total_energy
        
        return {
            "low_freq_ratio": float(low_freq_ratio),
            "natural_energy_dist": low_freq_ratio > LOW_FREQ_ENERGY_MIN
        }
