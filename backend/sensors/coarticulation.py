"""
Coarticulation sensor for detecting unnatural phoneme transitions.

Adapted from RecApp's coarticulation.py to work with BaseSensor interface.
Analyzes formant transition patterns to detect physically impossible or
unnatural phoneme blending that indicates synthetic speech.
"""

import numpy as np
from typing import Optional
from .base import BaseSensor, SensorResult
# from .vocal_tract import VocalTractSensor  # Removed due to patent infringement concerns

# Detection thresholds
MIN_VOWEL_DURATION_MS = 50.0  # Minimum duration for a stable vowel
MAX_TRANSITION_SPEED_HZ_MS = 30.0  # Maximum formant transition speed (Hz/ms)
MIN_COARTICULATION_OVERLAP_MS = 20.0  # Minimum overlap between phonemes
FORMANT_STABILITY_THRESHOLD = 50.0  # Hz variance for stable vowel

TRANSITION_CONSTRAINTS = {
    "max_formant_velocity_hz_ms": 30.0,
    "min_formant_continuity": 0.8,
    "min_transition_duration_ms": 30.0,
}


class CoarticulationSensor(BaseSensor):
    """
    Coarticulation sensor that detects unnatural phoneme transitions.
    
    Analyzes the spectral transition between phonemes. Natural speech has
    smooth, continuous transitions due to the physical movement of articulators.
    Synthetic speech often has abrupt or mathematically interpolated transitions.
    """
    
    def __init__(
        self,
        n_formants: int = 2,
        frame_length_ms: float = 25.0,
        hop_length_ms: float = 10.0,
    ):
        """
        Initialize coarticulation sensor.
        
        Args:
            n_formants: Number of formants to track (default: 2 for F1, F2)
            frame_length_ms: Frame length in milliseconds
            hop_length_ms: Hop length in milliseconds
        """
        super().__init__("Coarticulation Sensor")
        self.n_formants = n_formants
        self.frame_length_ms = frame_length_ms
        self.hop_length_ms = hop_length_ms
        self.sample_rate = None # Will be set during analyze
        self.hop_length = None # Will be set during analyze
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze coarticulation patterns in audio.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with coarticulation analysis
        """
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )
        
        # Set runtime parameters
        self.sample_rate = samplerate
        self.hop_length = int(self.hop_length_ms * samplerate / 1000)
        
        try:
            # Extract formant trajectories
            formant_trajectories = self._extract_formant_trajectories(audio_data, samplerate)
            
            if formant_trajectories is None or len(formant_trajectories) < 3:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.5,
                    threshold=0.5,
                    detail="Insufficient voiced segments for coarticulation analysis"
                )
            
            # Analyze formant velocities
            velocity_anomaly, f1_vel, f2_vel, max_f1_vel, max_f2_vel = \
                self._analyze_formant_velocities(formant_trajectories)
            
            # Analyze transition smoothness
            smoothness_anomaly, continuity = \
                self._analyze_transition_smoothness(formant_trajectories)
            
            # Analyze anticipatory coarticulation
            anticipatory_score = \
                self._analyze_anticipatory_coarticulation(formant_trajectories)
            
            # Analyze carryover coarticulation
            carryover_score = \
                self._analyze_carryover_coarticulation(formant_trajectories)
            
            # Calculate overall coarticulation anomaly score
            overall_score = self._calculate_overall_score(
                velocity_anomaly,
                smoothness_anomaly,
                anticipatory_score,
                carryover_score,
            )
            
            # Determine passed status
            passed = overall_score < 0.5 if overall_score > 0.3 else None
            
            result = SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=round(overall_score, 3),
                threshold=0.5,
            )
            
            if overall_score > 0.5:
                result.reason = "UNNATURAL_COARTICULATION"
                result.detail = (
                    f"Coarticulation patterns indicate synthetic speech. "
                    f"Anomaly score: {overall_score:.2f} (velocity: {velocity_anomaly:.2f}, "
                    f"smoothness: {smoothness_anomaly:.2f})"
                )
            else:
                result.detail = (
                    f"Coarticulation patterns consistent with natural speech. "
                    f"Anomaly score: {overall_score:.2f}"
                )
            
            result.metadata = {
                "velocity_anomaly": round(velocity_anomaly, 3),
                "smoothness_anomaly": round(smoothness_anomaly, 3),
                "anticipatory_score": round(anticipatory_score, 3),
                "carryover_score": round(carryover_score, 3),
                "mean_f1_velocity": round(f1_vel, 2),
                "mean_f2_velocity": round(f2_vel, 2),
                "max_f1_velocity": round(max_f1_vel, 2),
                "max_f2_velocity": round(max_f2_vel, 2),
                "formant_continuity": round(continuity, 3),
            }
            
            return result
            
        except Exception as e:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                reason="ERROR",
                detail=f"Coarticulation analysis failed: {str(e)}"
            )
    
    def _extract_formant_trajectories(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> Optional[np.ndarray]:
        """Extract formant trajectories over time."""
        # Use vocal tract sensor's formant extraction method
        # Extract formants frame by frame
        frame_length = int(self.frame_length_ms * sr / 1000)
        hop_length = int(self.hop_length_ms * sr / 1000)
        
        if len(audio) < frame_length:
            return None
        
        trajectories = []
        
        for i in range(0, len(audio) - frame_length + 1, hop_length):
            frame = audio[i:i + frame_length]
            
            # Apply window
            windowed = frame * np.hamming(len(frame))
            
            # Skip silent frames
            if np.max(np.abs(windowed)) < 0.01:
                continue
            
            # Extract formants using LPC (simplified version)
            try:
                formants = self._extract_formants_frame(windowed, sr, self.n_formants)
                if formants and len(formants) == self.n_formants:
                    trajectories.append(formants)
            except Exception:
                continue
        
        if len(trajectories) < 3:
            return None
        
        return np.array(trajectories)
    
    def _extract_formants_frame(
        self,
        frame: np.ndarray,
        sr: int,
        n_formants: int,
    ) -> list[float]:
        """Extract formants from a single frame using LPC."""
        # Reuse vocal tract sensor's LPC method
        lpc_order = sr // 1000 + 2
        
        # FFT-based autocorrelation
        autocorr = self._autocorr_fft(frame)
        autocorr = autocorr[:lpc_order + 1]
        
        # Levinson-Durbin
        lpc_coeffs = self._levinson_durbin(autocorr, lpc_order)
        
        # Find roots
        roots = np.roots(lpc_coeffs)
        
        # Filter stable poles
        stable_mask = np.abs(roots) < 1.0
        stable_roots = roots[stable_mask]
        angles = np.angle(stable_roots)
        
        # Convert to Hz
        positive_mask = angles > 0
        positive_angles = angles[positive_mask]
        formants = (positive_angles * sr) / (2 * np.pi)
        
        # Sort and filter
        formants = np.sort(formants)
        formants = formants[(formants > 50) & (formants < 5000)]
        
        if len(formants) < n_formants:
            defaults = [500.0, 1500.0, 2500.0]
            formants_list = formants.tolist()
            for i in range(len(formants), n_formants):
                formants_list.append(defaults[i] if i < len(defaults) else defaults[-1])
            return formants_list[:n_formants]
        
        return formants[:n_formants].tolist()
    
    def _analyze_formant_velocities(
        self,
        formants: np.ndarray,
    ) -> tuple[float, float, float, float, float]:
        """Analyze formant transition velocities."""
        f1_trajectory = formants[:, 0]
        f2_trajectory = formants[:, 1] if formants.shape[1] > 1 else formants[:, 0]
        
        # Velocity = difference between frames
        f1_velocity = np.abs(np.diff(f1_trajectory))
        f2_velocity = np.abs(np.diff(f2_trajectory))
        
        # Convert to Hz/ms
        hop_ms = self.hop_length * 1000 / self.sample_rate
        f1_velocity_hz_ms = f1_velocity / hop_ms
        f2_velocity_hz_ms = f2_velocity / hop_ms
        
        mean_f1_vel = float(np.mean(f1_velocity_hz_ms))
        mean_f2_vel = float(np.mean(f2_velocity_hz_ms))
        max_f1_vel = float(np.max(f1_velocity_hz_ms))
        max_f2_vel = float(np.max(f2_velocity_hz_ms))
        
        # Check against physical constraints
        max_allowed = TRANSITION_CONSTRAINTS["max_formant_velocity_hz_ms"]
        
        anomaly_score = 0.0
        
        # Check for impossible velocities
        impossible_f1 = np.sum(f1_velocity_hz_ms > max_allowed)
        impossible_f2 = np.sum(f2_velocity_hz_ms > max_allowed)
        
        if impossible_f1 > 0 or impossible_f2 > 0:
            pct_impossible = (impossible_f1 + impossible_f2) / (2 * len(f1_velocity_hz_ms))
            anomaly_score = min(0.9, 0.5 + pct_impossible)
        else:
            anomaly_score = 0.1
        
        return anomaly_score, mean_f1_vel, mean_f2_vel, max_f1_vel, max_f2_vel
    
    def _analyze_transition_smoothness(
        self,
        formants: np.ndarray,
    ) -> tuple[float, float]:
        """Analyze smoothness of formant transitions."""
        f1_trajectory = formants[:, 0]
        f2_trajectory = formants[:, 1] if formants.shape[1] > 1 else formants[:, 0]
        
        # Rolling correlation between adjacent windows
        window_size = 5
        correlations = []
        
        for i in range(len(f1_trajectory) - window_size):
            window1 = f1_trajectory[i:i + window_size]
            window2 = f1_trajectory[i + 1:i + window_size + 1]
            
            if np.std(window1) > 0 and np.std(window2) > 0:
                corr = np.corrcoef(window1, window2)[0, 1]
                correlations.append(corr)
        
        if len(correlations) == 0:
            return 0.5, 0.5
        
        mean_continuity = float(np.mean(correlations))
        min_continuity = TRANSITION_CONSTRAINTS["min_formant_continuity"]
        
        anomaly_score = 0.0
        
        if mean_continuity < min_continuity:
            anomaly_score = 0.7
        elif mean_continuity > 0.95:
            anomaly_score = 0.6
        else:
            anomaly_score = 0.1
        
        return anomaly_score, mean_continuity
    
    def _analyze_anticipatory_coarticulation(
        self,
        formants: np.ndarray,
    ) -> float:
        """Analyze anticipatory coarticulation patterns."""
        f1_trajectory = formants[:, 0]
        
        # Detect transitions
        f1_diff = np.abs(np.diff(f1_trajectory))
        threshold = np.percentile(f1_diff, 75)
        
        transition_indices = np.where(f1_diff > threshold)[0]
        
        if len(transition_indices) < 3:
            return 0.5
        
        # Measure transition duration
        transition_durations = []
        
        for idx in transition_indices:
            start_idx = idx
            for i in range(idx - 1, max(0, idx - 10), -1):
                if f1_diff[i] < threshold * 0.3:
                    start_idx = i
                    break
            
            duration = idx - start_idx
            transition_durations.append(duration)
        
        mean_duration = np.mean(transition_durations)
        min_duration = TRANSITION_CONSTRAINTS["min_transition_duration_ms"]
        hop_ms = self.hop_length * 1000 / self.sample_rate
        min_frames = min_duration / hop_ms
        
        if mean_duration < min_frames:
            anomaly_score = 0.7
        else:
            anomaly_score = 0.15
        
        return float(anomaly_score)
    
    def _analyze_carryover_coarticulation(
        self,
        formants: np.ndarray,
    ) -> float:
        """Analyze carryover coarticulation patterns."""
        f1_trajectory = formants[:, 0]
        
        # Calculate acceleration (second derivative)
        f1_accel = np.diff(np.diff(f1_trajectory))
        mean_abs_accel = np.mean(np.abs(f1_accel))
        
        # Threshold based on typical values
        if mean_abs_accel < 5.0:
            anomaly_score = 0.65
        else:
            anomaly_score = 0.2
        
        return float(anomaly_score)
    
    def _calculate_overall_score(
        self,
        velocity_anomaly: float,
        smoothness_anomaly: float,
        anticipatory_score: float,
        carryover_score: float,
    ) -> float:
        """Calculate overall coarticulation anomaly score."""
        weights = {
            "velocity": 0.30,
            "smoothness": 0.25,
            "anticipatory": 0.25,
            "carryover": 0.20,
        }
        
        overall = (
            weights["velocity"] * velocity_anomaly
            + weights["smoothness"] * smoothness_anomaly
            + weights["anticipatory"] * anticipatory_score
            + weights["carryover"] * carryover_score
        )
        
        return float(np.clip(overall, 0.0, 1.0))
    
    def _autocorr_fft(self, x: np.ndarray) -> np.ndarray:
        """Compute autocorrelation using FFT."""
        n = len(x)
        padded = np.pad(x, (0, n), mode='constant')
        fft_x = np.fft.fft(padded)
        autocorr = np.fft.ifft(fft_x * np.conj(fft_x))
        return np.real(autocorr[:n])
    
    def _levinson_durbin(
        self,
        autocorr: np.ndarray,
        order: int,
    ):
        """Levinson-Durbin recursion for LPC coefficient calculation."""
        lpc = np.zeros(order + 1)
        lpc[0] = 1.0
        
        error = autocorr[0]
        
        for i in range(order):
            if error == 0:
                break
            
            reflection = autocorr[i + 1]
            for j in range(1, i + 1):
                reflection -= lpc[j] * autocorr[i + 1 - j]
            reflection /= error
            
            lpc[i + 1] = reflection
            for j in range(1, (i + 2) // 2 + 1):
                temp = lpc[j]
                lpc[j] = temp - reflection * lpc[i + 1 - j]
                if j != i + 1 - j:
                    lpc[i + 1 - j] -= reflection * temp
            
            error *= 1 - reflection * reflection
        
        return lpc

