"""
Prosodic Continuity Sensor - Detects Abrupt Prosodic Changes.

This sensor analyzes the continuity of prosodic features (pitch, energy, timbre)
in speech to detect synthetic or spliced audio. Natural human speech exhibits
smooth transitions in these features, while synthesized or edited audio often
contains abrupt discontinuities.

Detection Strategy:
1. Use VAD to focus on speech segments only
2. Extract frame-based features:
   - RMS energy
   - Spectral centroid (timbre proxy)
   - F0 via autocorrelation (pitch)
3. Compute frame-to-frame deltas and normalize via z-scores
4. Flag "prosodic breaks" where z-scores exceed thresholds
5. Calculate risk score from break frequency

Key Features:
- Physics-based analysis (no ML models)
- No librosa dependency (uses numpy + scipy only)
- Handles edge cases gracefully
- Returns JSON-safe native types
"""

import logging
from typing import List, Dict, Tuple, Optional

import numpy as np
from scipy import signal

from backend.sensors.base import BaseSensor, SensorResult
from backend.sensors.vad import VoiceActivityDetector, SpeechSegment
from backend.utils.config import get_threshold

logger = logging.getLogger(__name__)


class ProsodicContinuitySensor(BaseSensor):
    """
    Analyzes prosodic continuity to detect synthetic or spliced speech.
    
    Natural speech has smooth prosodic contours. Synthetic speech and
    audio splicing often introduce abrupt changes in pitch, energy, or
    timbre that violate natural speech production constraints.
    
    This sensor:
    1. Identifies speech segments using VAD
    2. Extracts prosodic features (F0, energy, centroid) per frame
    3. Computes frame-to-frame deltas and z-scores
    4. Counts "prosodic breaks" (abnormal discontinuities)
    5. Returns risk score based on break frequency
    """
    
    # Frame parameters
    FRAME_SIZE_MS = 25
    HOP_SIZE_MS = 10
    
    # F0 estimation range (Hz)
    F0_MIN = 70
    F0_MAX = 400
    
    def __init__(self, category: str = "prosecution"):
        """
        Initialize ProsodicContinuitySensor.
        
        Args:
            category: "prosecution" (detects fake)
        """
        super().__init__("ProsodicContinuitySensor", category=category)
        
        # Load thresholds from config
        self.max_breaks_per_second = get_threshold(
            "prosodic_continuity",
            "max_breaks_per_second",
            default=2.0
        )
        self.risk_threshold = get_threshold(
            "prosodic_continuity",
            "risk_threshold",
            default=0.7
        )
        self.f0_zscore_threshold = get_threshold(
            "prosodic_continuity",
            "f0_zscore_threshold",
            default=3.0
        )
        self.energy_zscore_threshold = get_threshold(
            "prosodic_continuity",
            "energy_zscore_threshold",
            default=3.0
        )
        self.centroid_zscore_threshold = get_threshold(
            "prosodic_continuity",
            "centroid_zscore_threshold",
            default=3.0
        )
        self.min_speech_duration = get_threshold(
            "prosodic_continuity",
            "min_speech_duration",
            default=0.5
        )
        
        # Initialize VAD
        self.vad = VoiceActivityDetector()
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze prosodic continuity in audio.
        
        Args:
            audio_data: Audio signal as numpy array (mono, float)
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with risk score and details
        """
        try:
            # Input validation
            if not self.validate_input(audio_data, samplerate):
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.0,
                    threshold=self.risk_threshold,
                    reason="INVALID_INPUT",
                    detail="Invalid or empty audio input"
                )
            
            # Detect speech segments
            speech_segments = self.vad.detect_speech_segments(audio_data, samplerate)
            
            if not speech_segments:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.0,
                    threshold=self.risk_threshold,
                    reason="NO_SPEECH",
                    detail="No speech segments detected in audio"
                )
            
            # Calculate total speech duration
            total_speech_duration = sum(seg.duration_seconds for seg in speech_segments)
            
            if total_speech_duration < self.min_speech_duration:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.0,
                    threshold=self.risk_threshold,
                    reason="INSUFFICIENT_SPEECH",
                    detail=f"Total speech duration {total_speech_duration:.2f}s is below minimum {self.min_speech_duration}s"
                )
            
            # Extract features from speech frames
            features = self._extract_speech_features(
                audio_data, samplerate, speech_segments
            )
            
            if features is None or len(features['f0']) < 10:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.0,
                    threshold=self.risk_threshold,
                    reason="INSUFFICIENT_FRAMES",
                    detail="Too few frames for reliable analysis"
                )
            
            # Compute prosodic breaks
            breaks_info = self._detect_prosodic_breaks(features)
            
            # Calculate risk score
            breaks_per_second = breaks_info['total_breaks'] / total_speech_duration
            
            # Normalize to risk score [0, 1]
            risk_score = min(1.0, breaks_per_second / self.max_breaks_per_second)
            
            # Determine pass/fail
            passed = risk_score < self.risk_threshold
            
            # Build detail message
            detail = self._build_detail_message(
                breaks_info,
                breaks_per_second,
                total_speech_duration,
                passed
            )
            
            return SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=float(risk_score),
                threshold=float(self.risk_threshold),
                reason="PROSODIC_DISCONTINUITY" if not passed else None,
                detail=detail,
                metadata={
                    'total_breaks': int(breaks_info['total_breaks']),
                    'breaks_per_second': float(breaks_per_second),
                    'pitch_breaks': int(breaks_info['pitch_breaks']),
                    'energy_breaks': int(breaks_info['energy_breaks']),
                    'centroid_breaks': int(breaks_info['centroid_breaks']),
                    'total_speech_duration': float(total_speech_duration),
                    'num_speech_segments': len(speech_segments)
                }
            )
            
        except Exception as e:
            logger.error(f"Prosodic continuity analysis failed: {e}", exc_info=True)
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=self.risk_threshold,
                reason="ERROR",
                detail=f"Analysis failed: {str(e)}"
            )
    
    def _extract_speech_features(
        self,
        audio_data: np.ndarray,
        samplerate: int,
        speech_segments: List[SpeechSegment]
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Extract prosodic features from speech frames only.
        
        Args:
            audio_data: Full audio signal
            samplerate: Sample rate in Hz
            speech_segments: List of detected speech segments
            
        Returns:
            Dictionary containing feature arrays or None if failed
        """
        frame_size = int(self.FRAME_SIZE_MS * samplerate / 1000)
        hop_size = int(self.HOP_SIZE_MS * samplerate / 1000)
        
        # Check if signal is long enough
        if len(audio_data) < frame_size:
            return None
        
        # Lists to accumulate features from speech segments
        all_f0 = []
        all_energy = []
        all_centroid = []
        
        for segment in speech_segments:
            start_sample = int(segment.start_seconds * samplerate)
            end_sample = int(segment.end_seconds * samplerate)
            segment_audio = audio_data[start_sample:end_sample]
            
            if len(segment_audio) < frame_size:
                continue
            
            # Extract features for this segment
            f0_values, energy_values, centroid_values = self._extract_frame_features(
                segment_audio, samplerate, frame_size, hop_size
            )
            
            all_f0.extend(f0_values)
            all_energy.extend(energy_values)
            all_centroid.extend(centroid_values)
        
        if not all_f0:
            return None
        
        return {
            'f0': np.array(all_f0),
            'energy': np.array(all_energy),
            'centroid': np.array(all_centroid)
        }
    
    def _extract_frame_features(
        self,
        audio: np.ndarray,
        samplerate: int,
        frame_size: int,
        hop_size: int
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract frame-by-frame prosodic features.
        
        Args:
            audio: Audio segment
            samplerate: Sample rate in Hz
            frame_size: Frame size in samples
            hop_size: Hop size in samples
            
        Returns:
            Tuple of (f0_values, energy_values, centroid_values)
        """
        f0_values = []
        energy_values = []
        centroid_values = []
        
        num_frames = (len(audio) - frame_size) // hop_size + 1
        
        for i in range(num_frames):
            start = i * hop_size
            end = start + frame_size
            frame = audio[start:end]
            
            # Apply window
            windowed = frame * np.hamming(len(frame))
            
            # RMS energy
            rms = np.sqrt(np.mean(windowed ** 2))
            energy_values.append(rms)
            
            # Spectral centroid via FFT
            centroid = self._compute_spectral_centroid(windowed, samplerate)
            centroid_values.append(centroid)
            
            # F0 via autocorrelation
            f0 = self._estimate_f0_autocorr(windowed, samplerate)
            f0_values.append(f0)
        
        return f0_values, energy_values, centroid_values
    
    def _compute_spectral_centroid(self, frame: np.ndarray, samplerate: int) -> float:
        """
        Compute spectral centroid using FFT.
        
        Args:
            frame: Windowed frame
            samplerate: Sample rate in Hz
            
        Returns:
            Spectral centroid in Hz
        """
        # Compute FFT
        fft_size = len(frame)
        spectrum = np.abs(np.fft.rfft(frame))
        freqs = np.fft.rfftfreq(fft_size, 1.0 / samplerate)
        
        # Compute centroid (frequency-weighted average)
        if np.sum(spectrum) > 1e-10:
            centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
        else:
            centroid = 0.0
        
        return centroid
    
    def _estimate_f0_autocorr(self, frame: np.ndarray, samplerate: int) -> float:
        """
        Estimate F0 using autocorrelation method.
        
        Args:
            frame: Windowed frame
            samplerate: Sample rate in Hz
            
        Returns:
            F0 in Hz, or np.nan if unvoiced
        """
        # Compute autocorrelation
        autocorr = np.correlate(frame, frame, mode='full')
        autocorr = autocorr[len(autocorr) // 2:]
        
        # Normalize
        if autocorr[0] > 1e-10:
            autocorr = autocorr / autocorr[0]
        else:
            return np.nan
        
        # Find lag corresponding to F0 range
        min_lag = int(samplerate / self.F0_MAX)
        max_lag = int(samplerate / self.F0_MIN)
        
        if max_lag >= len(autocorr):
            max_lag = len(autocorr) - 1
        
        if min_lag >= max_lag:
            return np.nan
        
        # Find peak in autocorrelation within lag range
        search_region = autocorr[min_lag:max_lag]
        
        if len(search_region) == 0:
            return np.nan
        
        peak_lag = np.argmax(search_region) + min_lag
        
        # Check if peak is significant (voiced vs unvoiced)
        if autocorr[peak_lag] < 0.3:  # Threshold for voicing
            return np.nan
        
        # Convert lag to F0
        f0 = samplerate / peak_lag
        
        # Sanity check
        if f0 < self.F0_MIN or f0 > self.F0_MAX:
            return np.nan
        
        return f0
    
    def _detect_prosodic_breaks(self, features: Dict[str, np.ndarray]) -> Dict[str, int]:
        """
        Detect prosodic breaks based on z-scored deltas.
        
        Args:
            features: Dictionary of feature arrays
            
        Returns:
            Dictionary with break counts
        """
        pitch_breaks = 0
        energy_breaks = 0
        centroid_breaks = 0
        
        # Process F0 (voiced frames only)
        f0 = features['f0']
        voiced_mask = ~np.isnan(f0)
        voiced_f0 = f0[voiced_mask]
        
        if len(voiced_f0) > 2:
            f0_deltas = np.diff(voiced_f0)
            if len(f0_deltas) > 0 and np.std(f0_deltas) > 1e-6:
                f0_zscores = (f0_deltas - np.mean(f0_deltas)) / np.std(f0_deltas)
                pitch_breaks = int(np.sum(np.abs(f0_zscores) > self.f0_zscore_threshold))
        
        # Process energy
        energy = features['energy']
        if len(energy) > 1:
            energy_deltas = np.diff(energy)
            if len(energy_deltas) > 0 and np.std(energy_deltas) > 1e-6:
                energy_zscores = (energy_deltas - np.mean(energy_deltas)) / np.std(energy_deltas)
                energy_breaks = int(np.sum(np.abs(energy_zscores) > self.energy_zscore_threshold))
        
        # Process centroid
        centroid = features['centroid']
        if len(centroid) > 1:
            centroid_deltas = np.diff(centroid)
            if len(centroid_deltas) > 0 and np.std(centroid_deltas) > 1e-6:
                centroid_zscores = (centroid_deltas - np.mean(centroid_deltas)) / np.std(centroid_deltas)
                centroid_breaks = int(np.sum(np.abs(centroid_zscores) > self.centroid_zscore_threshold))
        
        total_breaks = pitch_breaks + energy_breaks + centroid_breaks
        
        return {
            'total_breaks': total_breaks,
            'pitch_breaks': pitch_breaks,
            'energy_breaks': energy_breaks,
            'centroid_breaks': centroid_breaks
        }
    
    def _build_detail_message(
        self,
        breaks_info: Dict[str, int],
        breaks_per_second: float,
        total_speech_duration: float,
        passed: bool
    ) -> str:
        """
        Build human-readable detail message.
        
        Args:
            breaks_info: Dictionary of break counts
            breaks_per_second: Normalized break rate
            total_speech_duration: Total speech duration in seconds
            passed: Whether analysis passed
            
        Returns:
            Detail message string
        """
        dominant_factors = []
        
        if breaks_info['pitch_breaks'] > 0:
            dominant_factors.append(f"pitch ({breaks_info['pitch_breaks']} breaks)")
        if breaks_info['energy_breaks'] > 0:
            dominant_factors.append(f"energy ({breaks_info['energy_breaks']} breaks)")
        if breaks_info['centroid_breaks'] > 0:
            dominant_factors.append(f"timbre ({breaks_info['centroid_breaks']} breaks)")
        
        if passed:
            if not dominant_factors:
                return f"Smooth prosodic contours detected in {total_speech_duration:.1f}s of speech"
            else:
                factors_str = ", ".join(dominant_factors)
                return f"Natural prosodic variation detected: {factors_str} in {total_speech_duration:.1f}s"
        else:
            if not dominant_factors:
                dominant_factors.append("multiple factors")
            factors_str = ", ".join(dominant_factors)
            return (
                f"Abrupt prosodic changes detected: {breaks_info['total_breaks']} breaks "
                f"({breaks_per_second:.2f}/sec) dominated by {factors_str}"
            )
