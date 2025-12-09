"""
Breathing Pattern Sensor for Deepfake Detection

Analyzes breathing regularity using spectral analysis to distinguish authentic
from synthetic audio. Real human breathing has natural variability in timing,
while synthetic audio often exhibits unnaturally regular breathing patterns.

Detection Strategy:
- Extract 20-300Hz frequency content (typical breathing frequency range)
- Identify breath events from spectral energy peaks
- Calculate inter-breath interval variance
- High variance = irregular (authentic) breathing
- Low variance = regular (synthetic) breathing

Output: Breathing regularity score (0-1)
- Score close to 1: Irregular breathing (authentic)
- Score close to 0: Regular breathing (synthetic/suspicious)
"""

import numpy as np
import librosa
from .base import BaseSensor, SensorResult
from backend.utils.config import get_threshold

# Constants - can be overridden by config/settings.yaml
BREATH_FREQ_MIN = 20  # Hz - lower bound of breathing frequency range
BREATH_FREQ_MAX = 300  # Hz - upper bound of breathing frequency range
MIN_BREATH_INTERVAL = 1.0  # seconds - minimum time between breaths
MAX_BREATH_INTERVAL = 8.0  # seconds - maximum time between breaths
MIN_VARIANCE_THRESHOLD = get_threshold("breathing_pattern", "min_variance", 0.3)
# Variance threshold: below this = regular (synthetic), above = irregular (authentic)

# SNR gating parameters
SNR_THRESHOLD_DB = get_threshold("breathing_pattern", "snr_threshold_db", 10.0)
# Minimum SNR in dB - reject analysis if background noise is too high


class BreathingPatternSensor(BaseSensor):
    """
    Breathing pattern sensor that analyzes breathing regularity for deepfake detection.

    Uses spectral analysis to extract breathing events in the 20-300Hz range,
    then calculates inter-breath interval variance. High variance indicates
    natural, irregular breathing (authentic), while low variance suggests
    synthetic audio with artificially regular breathing patterns.

    Includes SNR gating to reject analysis when background noise is too high,
    which would interfere with accurate breath detection.
    """

    def __init__(
        self,
        breath_freq_min: float = BREATH_FREQ_MIN,
        breath_freq_max: float = BREATH_FREQ_MAX,
        min_variance_threshold: float = MIN_VARIANCE_THRESHOLD,
        snr_threshold_db: float = SNR_THRESHOLD_DB,
    ):
        """
        Initialize breathing pattern sensor.

        Args:
            breath_freq_min: Minimum frequency for breath detection (Hz, default: 20)
            breath_freq_max: Maximum frequency for breath detection (Hz, default: 300)
            min_variance_threshold: Minimum variance for authentic breathing (default: 0.3)
            snr_threshold_db: Minimum SNR in dB to proceed with analysis (default: 10.0)
        """
        super().__init__("Breathing Pattern Sensor (Regularity Analysis)")
        self.breath_freq_min = breath_freq_min
        self.breath_freq_max = breath_freq_max
        self.min_variance_threshold = min_variance_threshold
        self.snr_threshold_db = snr_threshold_db

    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for breathing pattern regularity.

        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz

        Returns:
            SensorResult with breathing regularity score (0-1)
        """
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=None,  # Info-only sensor
                value=0.5,  # Neutral score
                threshold=self.min_variance_threshold,
                detail="Invalid or empty audio input."
            )

        # Check SNR - reject if too noisy
        snr_db = self._calculate_snr(audio_data)
        if snr_db < self.snr_threshold_db:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.5,  # Neutral score
                threshold=self.min_variance_threshold,
                detail=f"SNR too low ({snr_db:.1f} dB < {self.snr_threshold_db} dB). "
                       f"Background noise too high for reliable breath detection.",
                metadata={"snr_db": round(snr_db, 2), "rejected": True}
            )

        # Extract breathing frequency content (20-300Hz)
        breath_signal = self._extract_breath_frequencies(audio_data, samplerate)

        # Identify breath events
        breath_times = self._detect_breath_events(breath_signal, samplerate)

        if len(breath_times) < 2:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.5,  # Neutral score
                threshold=self.min_variance_threshold,
                detail=f"Insufficient breath events detected ({len(breath_times)}). "
                       f"Need at least 2 for interval analysis.",
                metadata={
                    "snr_db": round(snr_db, 2),
                    "breath_event_count": len(breath_times),
                }
            )

        # Calculate inter-breath intervals
        intervals = np.diff(breath_times)

        # Filter intervals to reasonable range
        valid_intervals = intervals[
            (intervals >= MIN_BREATH_INTERVAL) & (intervals <= MAX_BREATH_INTERVAL)
        ]

        if len(valid_intervals) < 2:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.5,
                threshold=self.min_variance_threshold,
                detail=f"Insufficient valid breath intervals ({len(valid_intervals)}). "
                       f"Need at least 2 for variance calculation.",
                metadata={
                    "snr_db": round(snr_db, 2),
                    "breath_event_count": len(breath_times),
                    "valid_interval_count": len(valid_intervals),
                }
            )

        # Calculate coefficient of variation (CV) = std / mean
        # CV normalizes variance by mean, making it scale-invariant
        mean_interval = np.mean(valid_intervals)
        std_interval = np.std(valid_intervals)
        cv = std_interval / mean_interval if mean_interval > 0 else 0.0

        # Convert CV to regularity score (0-1)
        # High CV (high variance) -> score close to 1 (irregular, authentic)
        # Low CV (low variance) -> score close to 0 (regular, synthetic)
        # Use sigmoid-like mapping for smooth transition
        regularity_score = min(1.0, cv / self.min_variance_threshold)

        # Determine if breathing pattern is suspicious
        passed = bool(regularity_score >= 0.5)  # Pass if variance is reasonable

        result = SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=round(regularity_score, 3),
            threshold=self.min_variance_threshold,
            metadata={
                "snr_db": round(snr_db, 2),
                "breath_event_count": len(breath_times),
                "valid_interval_count": len(valid_intervals),
                "mean_interval_seconds": round(mean_interval, 2),
                "std_interval_seconds": round(std_interval, 2),
                "coefficient_of_variation": round(cv, 3),
            }
        )

        if not passed:
            result.reason = "SYNTHETIC_BREATHING_PATTERN"
            result.detail = (
                f"Breathing pattern is unnaturally regular (CV: {cv:.3f}). "
                f"Real human breathing shows more temporal variability. "
                f"Regularity score: {regularity_score:.3f}"
            )
        else:
            result.detail = (
                f"Breathing pattern shows natural variability (CV: {cv:.3f}). "
                f"Regularity score: {regularity_score:.3f}"
            )

        return result

    def _calculate_snr(self, audio: np.ndarray) -> float:
        """
        Calculate Signal-to-Noise Ratio (SNR) in dB.

        Uses a simple approach: assumes the top 50% energy frames are signal,
        and bottom 20% are noise.

        Args:
            audio: Audio signal

        Returns:
            SNR in dB
        """
        # Compute frame-wise energy
        frame_length = 2048
        hop_length = 512

        # Use RMS energy per frame
        rms = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]

        if len(rms) < 10:
            return 0.0  # Too short to estimate SNR

        # Sort RMS values
        rms_sorted = np.sort(rms)

        # Estimate noise from bottom 20% percentile
        noise_percentile = int(len(rms_sorted) * 0.2)
        noise_rms = np.mean(rms_sorted[:max(1, noise_percentile)])

        # Estimate signal from top 50% percentile
        signal_start = int(len(rms_sorted) * 0.5)
        signal_rms = np.mean(rms_sorted[signal_start:])

        # Calculate SNR in dB
        if noise_rms > 0:
            snr_db = 20 * np.log10(signal_rms / noise_rms)
        else:
            snr_db = 100.0  # Very high SNR (no noise)

        return float(snr_db)

    def _extract_breath_frequencies(
        self,
        audio: np.ndarray,
        sr: int
    ) -> np.ndarray:
        """
        Extract 20-300Hz frequency content using bandpass filtering.

        This frequency range captures breathing sounds while filtering out
        most speech content (which is primarily above 300Hz for formants).

        Args:
            audio: Input audio signal
            sr: Sample rate

        Returns:
            Filtered audio containing only breathing frequency content
        """
        # Use Short-Time Fourier Transform (STFT) for frequency-domain filtering
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)

        # Get frequency bins
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

        # Create bandpass mask for 20-300Hz
        mask = (freqs >= self.breath_freq_min) & (freqs <= self.breath_freq_max)

        # Apply mask - zero out frequencies outside breathing range
        stft_filtered = stft.copy()
        stft_filtered[~mask, :] = 0

        # Convert back to time domain
        breath_signal = librosa.istft(stft_filtered, hop_length=512)

        # Ensure output length matches input
        if len(breath_signal) > len(audio):
            breath_signal = breath_signal[:len(audio)]
        elif len(breath_signal) < len(audio):
            breath_signal = np.pad(breath_signal, (0, len(audio) - len(breath_signal)))

        return breath_signal

    def _detect_breath_events(
        self,
        breath_signal: np.ndarray,
        sr: int
    ) -> np.ndarray:
        """
        Detect breath events from filtered breath signal.

        Uses energy envelope detection and peak finding to identify
        individual breath events.

        Args:
            breath_signal: Bandpass-filtered breath signal
            sr: Sample rate

        Returns:
            Array of breath event times in seconds
        """
        # Compute energy envelope
        envelope = np.abs(librosa.feature.rms(
            y=breath_signal,
            frame_length=2048,
            hop_length=512
        )[0])

        if len(envelope) == 0:
            return np.array([])

        # Smooth envelope
        from scipy.ndimage import gaussian_filter1d
        envelope_smooth = gaussian_filter1d(envelope, sigma=2.0)

        # Find peaks in envelope (breath events)
        from scipy.signal import find_peaks

        # Adaptive threshold: use median + 1.5 * MAD (Median Absolute Deviation)
        median_env = np.median(envelope_smooth)
        mad = np.median(np.abs(envelope_smooth - median_env))
        threshold = median_env + 1.5 * mad

        # Minimum distance between breaths: 1 second
        min_distance_frames = int(MIN_BREATH_INTERVAL * sr / 512)

        peaks, _ = find_peaks(
            envelope_smooth,
            height=threshold,
            distance=min_distance_frames
        )

        # Convert frame indices to time (seconds)
        breath_times = peaks * 512 / sr

        return breath_times
