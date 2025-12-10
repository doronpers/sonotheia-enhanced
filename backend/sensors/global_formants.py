"""
Global Formant Statistics Sensor.

Analyzes the long-term statistical distribution of spectral peaks (formants)
to detect synthetic speech.

Patent Safety:
- Uses Cepstral Envelope Smoothing (homomorphic filtering) to estimate spectral envelope.
- Does NOT use Linear Predictive Coding (LPC).
- Analyzes global statistics (mean, std, skew) rather than tracking specific trajectories.
"""

import numpy as np
from scipy import signal, stats
from typing import Dict
from .base import BaseSensor, SensorResult

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

class GlobalFormantSensor(BaseSensor):
    """
    Analyzes global statistics of the spectral envelope.
    
    Synthetic speech often exhibits:
    - Overly consistent formant bandwidths
    - Unnatural distribution of spectral energy (too flat or too peaked)
    - Missing "speaker identity" variance in long-term average spectrum (LTAS)
    
    Method:
    1. Compute Short-Time Fourier Transform (STFT).
    2. Compute Real Cepstrum.
    3. Apply low-pass lifter to extract Spectral Envelope.
    4. Analyze statistical properties of the envelope.
    """
    
    def __init__(self, n_fft: int = 2048, hop_length: int = 512, category: str = "defense"):
        super().__init__("Global Formant Stats", category=category)
        self.n_fft = n_fft
        self.hop_length = hop_length
        
    def analyze(self, audio: np.ndarray, sr: int) -> SensorResult:
        if not self.validate_input(audio, sr):
             return SensorResult(self.name, None, 0.0, 0.5, "Invalid input")
             
        try:
            # 1. Compute Spectral Envelope via Cepstral Analysis (No LPC)
            envelope = self._compute_cepstral_envelope(audio, sr)
            
            # 2. Analyze Statistics
            stats_results = self._analyze_envelope_statistics(envelope)
            
            # 3. Score
            score = self._compute_score(stats_results)
            
            passed = score < 0.5
            
            detail = f"Global formant stats passed. Score: {score:.2f}"
            if not passed:
                detail = f"Unnatural spectral envelope statistics. Score: {score:.2f}. " \
                         f"Kurtosis: {stats_results['kurtosis']:.2f}, Skew: {stats_results['skew']:.2f}"
            
            return SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=score,
                threshold=0.5,
                detail=detail,
                metadata=stats_results
            )
            
        except Exception as e:
            return SensorResult(self.name, None, 0.0, 0.5, "ERROR", str(e))

    def _compute_cepstral_envelope(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Compute spectral envelope using Cepstral smoothing (homomorphic filtering).
        This separates source (fine structure) from filter (envelope) without LPC.
        """
        # Pre-emphasis
        audio = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

        # Skip analysis if shorter than n_fft (padding distorts stats)
        # Pad if shorter than n_fft (padding distorts stats slightly but better than crashing)
        if len(audio) < self.n_fft:
             padding = self.n_fft - len(audio)
             audio = np.pad(audio, (0, padding), mode='constant')
        
        # STFT
        if HAS_LIBROSA:
            S = np.abs(librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length))
        else:
            f, t, S = signal.stft(audio, sr, nperseg=self.n_fft, noverlap=self.n_fft - self.hop_length)
            S = np.abs(S)
            
        # Log magnitude spectrum
        log_S = np.log(S + 1e-10)
        
        # Cepstrum (Inverse FFT of log spectrum)
        cepstrum = np.fft.ifft(log_S, axis=0).real
        
        # Low-pass lifter (keep only first few coefficients)
        # The first ~13-20 coefficients represent the spectral envelope (vocal tract)
        lifter_cutoff = 20
        cepstrum[lifter_cutoff:-lifter_cutoff] = 0
        
        # Transform back to spectral domain to get envelope
        log_envelope = np.fft.fft(cepstrum, axis=0).real
        envelope = np.exp(log_envelope)
        
        return envelope

    def _analyze_envelope_statistics(self, envelope: np.ndarray) -> Dict[str, float]:
        """
        Compute statistics of the spectral envelope.
        """
        # Average envelope over time (LTAS - Long Term Average Spectrum)
        ltas = np.mean(envelope, axis=1)
        
        # Normalize
        ltas = ltas / (np.max(ltas) + 1e-10)
        
        # Statistical moments
        mean = float(np.mean(ltas))
        std = float(np.std(ltas))
        skew = float(stats.skew(ltas))
        kurtosis = float(stats.kurtosis(ltas))
        
        # Spectral Flatness of the envelope (not the raw spectrum)
        # High flatness in envelope -> undefined formants (synthetic/robotic)
        flatness = float(stats.gmean(ltas + 1e-10) / (np.mean(ltas) + 1e-10))
        
        return {
            "mean": mean,
            "std": std,
            "skew": skew,
            "kurtosis": kurtosis,
            "flatness": flatness
        }

    def _compute_score(self, stats: Dict[str, float]) -> float:
        """
        Heuristic scoring based on natural speech statistics.
        Natural speech LTAS typically has specific shape (peaks at formants).
        """
        score = 0.0
        
        # Check for overly flat envelope (robotic)
        if stats["flatness"] > 0.4:
            score += 0.4
            
        # Check for unnatural distribution (kurtosis)
        # Natural speech has peaks (formants), so distribution of energy is not Gaussian
        # It should have tails.
        if stats["kurtosis"] < -1.0: # Too flat distribution
            score += 0.3
            
        # Check for lack of variance (std)
        if stats["std"] < 0.05:
            score += 0.3
            
        return min(1.0, score)
