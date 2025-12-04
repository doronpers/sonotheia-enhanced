"""
Formant Trajectory Sensor - Patent-Safe Vocal Tract Analysis

**Patent Compliance**: This implementation uses FORMANT TRAJECTORY VELOCITIES
(dynamic analysis) rather than static spectral values or Linear Predictive Coding error signals, 
providing freedom to operate around Pindrop's Source-Filter Theory patents.

**Design-Around Strategy**:
- ❌ RESTRICTED: Linear Predictive Coding error signals, glottal closing detection, static formant values
- ✅ SAFE: Formant velocity analysis, physiological speed limit detection

Detects synthetic speech by identifying physiologically impossible formant 
movement speeds (e.g., F1 moving >300 Hz in 10ms).
"""

import numpy as np
import librosa
from scipy.signal import find_peaks
from typing import Dict, Any, Optional, Tuple, List
import logging

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)


class FormantTrajectorySensor(BaseSensor):
    """
    Analyzes formant trajectories to detect synthetic speech.
    
    This sensor tracks the velocity of formant frequency changes over time.
    Synthetic speech often exhibits impossible physiological formant movements
    (e.g., formants changing too quickly for human vocal tract biomechanics).
    
    **Patent-Safe Approach**:
    - Uses spectral peak tracking (not LPC)
    - Analyzes dynamic trajectories (rate of change)
    - Detects violations of physiological speed limits
    - No source-filter theory application or residual analysis
    """
    
    # Physiological speed limits (Hz per 10ms frame)
    # Based on human vocal tract biomechanical constraints
    MAX_F1_VELOCITY = 300  # Hz per 10ms
    MAX_F2_VELOCITY = 500  # Hz per 10ms
    MAX_F3_VELOCITY = 500  # Hz per 10ms
    MAX_F4_VELOCITY = 600  # Hz per 10ms
    
    def __init__(self):
        super().__init__()
        self.name = "FormantTrajectory"
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze formant trajectories for physiologically impossible movements.
        
        Args:
            audio_data: Audio signal (normalized float32)
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult indicating if formant trajectories are natural
        """
        try:
            # Frame parameters
            frame_length = int(0.025 * samplerate)  # 25ms frames
            hop_length = int(0.010 * samplerate)    # 10ms hop (velocity reference)
            
            # Extract formant frequencies over time
            formant_tracks = self._extract_formant_tracks(
                audio_data, 
                samplerate, 
                frame_length, 
                hop_length
            )
            
            if formant_tracks is None or len(formant_tracks) == 0:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,
                    value=0.0,
                    threshold=0.0,
                    reason="Insufficient audio for formant tracking",
                    detail="Audio too short or low quality"
                )
            
            # Calculate formant velocities (Hz per 10ms)
            velocities = self._calculate_velocities(formant_tracks, hop_length, samplerate)
            
            # Check for physiologically impossible velocities
            max_velocity, formant_num = self._detect_impossible_velocities(velocities)
            
            # Threshold: any velocity exceeding physiological limits is suspicious
            # We use a normalized score: 0.0 = within limits, 1.0 = far exceeds limits
            threshold_velocity = self._get_threshold_for_formant(formant_num)
            
            if max_velocity <= threshold_velocity:
                # Normal physiological movement
                passed = True
                normalized_score = max_velocity / threshold_velocity
            else:
                # Impossible movement detected
                passed = False
                # Normalize: how much it exceeds limit (capped at 3x for score calculation)
                normalized_score = min(max_velocity / threshold_velocity, 3.0)
            
            return SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=float(normalized_score),
                threshold=1.0,  # Threshold is normalized to 1.0
                reason=f"Impossible F{formant_num} velocity: {max_velocity:.1f} Hz/10ms" if not passed else None,
                detail=f"Max formant velocity: F{formant_num} at {max_velocity:.1f} Hz/10ms (limit: {threshold_velocity} Hz/10ms)",
                metadata={
                    "max_velocity_hz_per_10ms": float(max_velocity),
                    "formant_number": int(formant_num),
                    "num_frames_analyzed": len(formant_tracks)
                }
            )
            
        except Exception as e:
            logger.error(f"Formant trajectory analysis failed: {e}", exc_info=True)
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.0,
                reason=f"Analysis failed: {str(e)}",
                detail=None
            )
    
    def _extract_formant_tracks(
        self, 
        audio_data: np.ndarray, 
        samplerate: int,
        frame_length: int,
        hop_length: int
    ) -> Optional[np.ndarray]:
        """
        Extract formant frequency tracks over time using spectral peak tracking.
        
        **Patent-Safe Method**: Uses spectral analysis (not LPC).
        
        Returns:
            Array of shape (num_frames, 4) containing F1-F4 frequencies in Hz,
            or None if extraction fails
        """
        # Apply pre-emphasis to enhance formants
        pre_emphasized = librosa.effects.preemphasis(audio_data)
        
        # Frame the signal
        frames = librosa.util.frame(
            pre_emphasized, 
            frame_length=frame_length, 
            hop_length=hop_length
        )
        
        formant_tracks = []
        
        for i in range(frames.shape[1]):
            frame = frames[:, i]
            
            # Apply window
            windowed = frame * np.hamming(len(frame))
            
            # Skip silent frames
            if np.sum(windowed**2) < 1e-10:
                # Use previous frame's formants or zeros
                if len(formant_tracks) > 0:
                    formant_tracks.append(formant_tracks[-1].copy())
                else:
                    formant_tracks.append(np.zeros(4))
                continue
            
            # Compute power spectrum
            fft_size = 2048
            spectrum = np.fft.rfft(windowed, n=fft_size)
            power_spectrum = np.abs(spectrum) ** 2
            
            # Convert to dB
            power_db = 10 * np.log10(power_spectrum + 1e-10)
            
            # Find spectral peaks (formant candidates)
            formants = self._find_formant_peaks(power_db, samplerate, fft_size)
            
            formant_tracks.append(formants)
        
        if len(formant_tracks) == 0:
            return None
        
        return np.array(formant_tracks)
    
    def _find_formant_peaks(
        self, 
        power_db: np.ndarray, 
        samplerate: int, 
        fft_size: int
    ) -> np.ndarray:
        """
        Find formant frequencies from power spectrum using peak detection.
        
        Args:
            power_db: Power spectrum in dB
            samplerate: Sample rate
            fft_size: FFT size
            
        Returns:
            Array of 4 formant frequencies [F1, F2, F3, F4] in Hz
        """
        # Frequency resolution
        freq_resolution = samplerate / fft_size
        frequencies = np.fft.rfftfreq(fft_size, 1.0 / samplerate)
        
        # Find peaks with prominence threshold
        peaks, properties = find_peaks(power_db, prominence=10, distance=10)
        
        if len(peaks) == 0:
            return np.zeros(4)
        
        # Sort peaks by prominence
        prominences = properties['prominences']
        sorted_indices = np.argsort(prominences)[::-1]
        sorted_peaks = peaks[sorted_indices]
        
        # Expected formant ranges (Hz) for adult speakers
        formant_ranges = [
            (200, 1000),   # F1
            (800, 2500),   # F2
            (1800, 3500),  # F3
            (2500, 4500),  # F4
        ]
        
        formants = np.zeros(4)
        
        # Match peaks to formant ranges
        for i, (f_min, f_max) in enumerate(formant_ranges):
            for peak in sorted_peaks:
                peak_freq = frequencies[peak]
                if f_min <= peak_freq <= f_max:
                    formants[i] = peak_freq
                    break
        
        return formants
    
    def _calculate_velocities(
        self, 
        formant_tracks: np.ndarray,
        hop_length: int,
        samplerate: int
    ) -> Dict[int, np.ndarray]:
        """
        Calculate formant velocities (rate of change) in Hz per 10ms.
        
        **Patent-Safe**: Focuses on DYNAMIC TRAJECTORIES (derivatives),
        not static spectral values.
        
        Args:
            formant_tracks: Array of shape (num_frames, 4)
            hop_length: Hop length in samples
            samplerate: Sample rate
            
        Returns:
            Dictionary mapping formant number (1-4) to velocity arrays
        """
        # Time per frame in seconds
        time_per_frame = hop_length / samplerate
        
        # Normalize to Hz per 10ms for comparison with physiological limits
        scale_factor = 0.01 / time_per_frame  # 10ms = 0.01s
        
        velocities = {}
        
        for formant_num in range(4):
            formant_track = formant_tracks[:, formant_num]
            
            # Calculate velocity (first derivative)
            velocity = np.diff(formant_track) * scale_factor
            
            # Take absolute values (we care about speed, not direction)
            velocity = np.abs(velocity)
            
            velocities[formant_num + 1] = velocity  # 1-indexed (F1, F2, F3, F4)
        
        return velocities
    
    def _detect_impossible_velocities(
        self, 
        velocities: Dict[int, np.ndarray]
    ) -> Tuple[float, int]:
        """
        Detect physiologically impossible formant velocities.
        
        Returns:
            Tuple of (max_velocity, formant_number)
        """
        thresholds = {
            1: self.MAX_F1_VELOCITY,
            2: self.MAX_F2_VELOCITY,
            3: self.MAX_F3_VELOCITY,
            4: self.MAX_F4_VELOCITY,
        }
        
        max_velocity = 0.0
        max_formant = 1
        
        for formant_num, velocity_array in velocities.items():
            if len(velocity_array) == 0:
                continue
            
            # Find maximum velocity for this formant
            formant_max = np.max(velocity_array)
            
            if formant_max > max_velocity:
                max_velocity = formant_max
                max_formant = formant_num
        
        return max_velocity, max_formant
    
    def _get_threshold_for_formant(self, formant_num: int) -> float:
        """Get physiological speed limit for a given formant."""
        thresholds = {
            1: self.MAX_F1_VELOCITY,
            2: self.MAX_F2_VELOCITY,
            3: self.MAX_F3_VELOCITY,
            4: self.MAX_F4_VELOCITY,
        }
        return thresholds.get(formant_num, self.MAX_F2_VELOCITY)
