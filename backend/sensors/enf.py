"""
Electrical Network Frequency (ENF) sensor for deepfake detection.

ENF analysis detects the 50/60Hz power grid frequency embedded in audio recordings
from electrical devices. Deepfakes often lack authentic ENF signatures or show
inconsistent patterns that reveal synthesis artifacts.

This sensor provides a unique differentiator from competitors by analyzing:
- ENF frequency stability (real recordings show natural grid variations)
- ENF phase continuity (synthetic audio often has phase discontinuities)
- Temporal ENF patterns (authentic recordings match known grid frequency databases)
"""

import logging
import numpy as np
from typing import Optional, Dict, Any, Tuple
from scipy import signal
from scipy.fft import fft, fftfreq

from .base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

# ENF frequency ranges (Hz) - varies by region
ENF_NOMINAL_50HZ = 50.0  # Europe, Asia, Africa, Australia
ENF_NOMINAL_60HZ = 60.0  # North America, parts of South America, Japan

# ENF detection parameters
ENF_BANDWIDTH_HZ = 0.1  # ±0.1Hz around nominal frequency
ENF_ANALYSIS_WINDOW_SEC = 1.0  # 1-second windows for temporal analysis
ENF_MIN_DURATION_SEC = 2.0  # Minimum audio duration for reliable ENF analysis

# Thresholds for ENF-based detection
ENF_STABILITY_THRESHOLD = 0.05  # Maximum frequency deviation (Hz) for authentic recordings
ENF_PHASE_CONTINUITY_THRESHOLD = 0.8  # Minimum phase correlation between windows
ENF_ABSENCE_PENALTY = 0.3  # Penalty score when ENF is completely absent (suspicious)


class ENFSensor(BaseSensor):
    """
    Electrical Network Frequency sensor for detecting authentic recording signatures.
    
    Analyzes the 50/60Hz power grid frequency embedded in audio recordings.
    Real recordings from devices connected to the electrical grid will contain
    ENF signatures that follow natural grid frequency variations. Deepfakes
    often lack these signatures or show inconsistent patterns.
    """
    
    def __init__(
        self,
        nominal_frequency: float = 60.0,
        analysis_window_sec: float = ENF_ANALYSIS_WINDOW_SEC,
        min_duration_sec: float = ENF_MIN_DURATION_SEC,
        stability_threshold: float = ENF_STABILITY_THRESHOLD,
        phase_continuity_threshold: float = ENF_PHASE_CONTINUITY_THRESHOLD,
    ):
        """
        Initialize ENF sensor.
        
        Args:
            nominal_frequency: Expected ENF frequency (50.0 or 60.0 Hz)
            analysis_window_sec: Window size in seconds for temporal analysis
            min_duration_sec: Minimum audio duration for reliable analysis
            stability_threshold: Maximum frequency deviation for authentic recordings
            phase_continuity_threshold: Minimum phase correlation between windows
        """
        super().__init__("ENF Sensor")
        self.nominal_frequency = nominal_frequency
        self.analysis_window_sec = analysis_window_sec
        self.min_duration_sec = min_duration_sec
        self.stability_threshold = stability_threshold
        self.phase_continuity_threshold = phase_continuity_threshold
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for Electrical Network Frequency signatures.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with ENF analysis
        """
        # Validate input
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )
        
        # Check minimum duration
        duration_seconds = len(audio_data) / samplerate
        if duration_seconds < self.min_duration_sec:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                reason="INSUFFICIENT_DURATION",
                detail=f"Audio too short for reliable ENF analysis "
                       f"({duration_seconds:.2f}s < {self.min_duration_sec:.2f}s minimum)",
                metadata={"duration_seconds": round(duration_seconds, 2)}
            )
        
        try:
            # Extract ENF features
            enf_features = self._extract_enf_features(audio_data, samplerate)
            
            if enf_features is None:
                # ENF not detected - suspicious for deepfakes
                return SensorResult(
                    sensor_name=self.name,
                    passed=False,
                    value=ENF_ABSENCE_PENALTY,
                    threshold=0.5,
                    reason="ENF_ABSENT",
                    detail="No ENF signature detected. Authentic recordings typically "
                           "contain 50/60Hz power grid frequency signatures from "
                           "electrical devices.",
                    metadata={
                        "enf_detected": False,
                        "nominal_frequency_hz": self.nominal_frequency,
                        "duration_seconds": round(duration_seconds, 2),
                    }
                )
            
            # Analyze ENF characteristics
            stability_score, phase_score, anomaly_score = self._analyze_enf_patterns(
                enf_features, audio_data, samplerate
            )
            
            # Determine if ENF pattern is authentic
            is_authentic = (
                stability_score >= (1.0 - self.stability_threshold / 0.1) and
                phase_score >= self.phase_continuity_threshold
            )
            
            # Calculate overall anomaly score (higher = more suspicious)
            overall_anomaly = 1.0 - (stability_score * 0.5 + phase_score * 0.5)
            
            result = SensorResult(
                sensor_name=self.name,
                passed=is_authentic,
                value=round(overall_anomaly, 3),
                threshold=0.5,
            )
            
            if not is_authentic:
                if stability_score < (1.0 - self.stability_threshold / 0.1):
                    result.reason = "ENF_UNSTABLE"
                    result.detail = (
                        f"ENF frequency shows unstable patterns inconsistent with "
                        f"authentic grid variations. Stability score: {stability_score:.3f}"
                    )
                elif phase_score < self.phase_continuity_threshold:
                    result.reason = "ENF_PHASE_DISCONTINUITY"
                    result.detail = (
                        f"ENF phase shows discontinuities suggesting synthetic "
                        f"audio manipulation. Phase continuity: {phase_score:.3f}"
                    )
                else:
                    result.reason = "ENF_ANOMALOUS"
                    result.detail = (
                        f"ENF pattern shows anomalies inconsistent with authentic "
                        f"recordings. Anomaly score: {overall_anomaly:.3f}"
                    )
            else:
                result.detail = (
                    f"ENF signature detected and validated. Frequency stability: "
                    f"{stability_score:.3f}, phase continuity: {phase_score:.3f}"
                )
            
            result.metadata = {
                "enf_detected": True,
                "nominal_frequency_hz": self.nominal_frequency,
                "detected_frequency_hz": round(enf_features["mean_frequency"], 3),
                "frequency_stability": round(stability_score, 3),
                "phase_continuity": round(phase_score, 3),
                "anomaly_score": round(overall_anomaly, 3),
                "duration_seconds": round(duration_seconds, 2),
                "sample_rate": samplerate,
            }
            
            return result
            
        except Exception as e:
            logger.error(f"ENF analysis failed: {str(e)}", exc_info=True)
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                reason="ERROR",
                detail=f"ENF analysis failed: {str(e)}"
            )
    
    def _extract_enf_features(
        self, audio_data: np.ndarray, samplerate: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract ENF frequency features from audio.
        
        Args:
            audio_data: Audio signal
            samplerate: Sample rate in Hz
            
        Returns:
            Dictionary with ENF features or None if not detected
        """
        # Convert to mono if stereo
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=0)
        
        # Apply bandpass filter around nominal ENF frequency
        nyquist = samplerate / 2
        low_cut = max(0.1, (self.nominal_frequency - ENF_BANDWIDTH_HZ * 2) / nyquist)
        high_cut = min(0.99, (self.nominal_frequency + ENF_BANDWIDTH_HZ * 2) / nyquist)
        
        if low_cut >= high_cut:
            return None
        
        # Design bandpass filter
        sos = signal.butter(4, [low_cut, high_cut], btype='band', output='sos')
        filtered_audio = signal.sosfilt(sos, audio_data)
        
        # Compute FFT for frequency analysis
        window_samples = int(self.analysis_window_sec * samplerate)
        if len(filtered_audio) < window_samples:
            window_samples = len(filtered_audio)
        
        # Use multiple overlapping windows for temporal analysis
        hop_samples = window_samples // 2
        frequencies = []
        phases = []
        
        for start in range(0, len(filtered_audio) - window_samples + 1, hop_samples):
            window = filtered_audio[start:start + window_samples]
            
            # Apply windowing function
            windowed = window * np.hanning(len(window))
            
            # Compute FFT
            fft_vals = fft(windowed)
            fft_freqs = fftfreq(len(windowed), 1.0 / samplerate)
            
            # Find peak in ENF band
            enf_band_mask = (
                (fft_freqs >= self.nominal_frequency - ENF_BANDWIDTH_HZ) &
                (fft_freqs <= self.nominal_frequency + ENF_BANDWIDTH_HZ)
            )
            
            if not np.any(enf_band_mask):
                continue
            
            enf_fft = fft_vals[enf_band_mask]
            enf_freqs = fft_freqs[enf_band_mask]
            
            # Find peak frequency
            peak_idx = np.argmax(np.abs(enf_fft))
            peak_freq = enf_freqs[peak_idx]
            peak_magnitude = np.abs(fft_vals[enf_band_mask][peak_idx])
            
            # Only include if magnitude is significant
            max_magnitude = np.max(np.abs(fft_vals))
            if peak_magnitude > max_magnitude * 0.01:  # At least 1% of max
                frequencies.append(peak_freq)
                phases.append(np.angle(fft_vals[enf_band_mask][peak_idx]))
        
        if len(frequencies) == 0:
            return None
        
        return {
            "frequencies": np.array(frequencies),
            "phases": np.array(phases),
            "mean_frequency": np.mean(frequencies),
            "std_frequency": np.std(frequencies),
        }
    
    def _analyze_enf_patterns(
        self,
        enf_features: Dict[str, Any],
        audio_data: np.ndarray,
        samplerate: int
    ) -> Tuple[float, float, float]:
        """
        Analyze ENF patterns for authenticity.
        
        Args:
            enf_features: Extracted ENF features
            audio_data: Original audio data
            samplerate: Sample rate
            
        Returns:
            Tuple of (stability_score, phase_score, anomaly_score)
            All scores range from 0.0 to 1.0
        """
        frequencies = enf_features["frequencies"]
        phases = enf_features["phases"]
        
        # Stability score: how consistent is the frequency?
        # Real grid frequency varies naturally but stays within narrow range
        freq_std = enf_features["std_frequency"]
        # Normalize: std < 0.05Hz is very stable, > 0.2Hz is unstable
        stability_score = max(0.0, 1.0 - (freq_std / 0.2))
        
        # Phase continuity score: how continuous is the phase?
        # Real recordings have smooth phase transitions
        if len(phases) > 1:
            phase_diffs = np.diff(phases)
            # Unwrap phase differences
            phase_diffs = np.unwrap(phase_diffs)
            # Calculate phase correlation (lower variance = more continuous)
            phase_variance = np.var(phase_diffs)
            # Normalize: variance < 0.1 is very continuous, > 1.0 is discontinuous
            phase_score = max(0.0, 1.0 - min(1.0, phase_variance))
        else:
            phase_score = 0.5  # Can't determine with single window
        
        # Overall anomaly score (higher = more suspicious)
        anomaly_score = 1.0 - (stability_score * 0.5 + phase_score * 0.5)
        
        return stability_score, phase_score, anomaly_score
