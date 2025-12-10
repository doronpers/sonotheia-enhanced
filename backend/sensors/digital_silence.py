"""
Digital Silence sensor for detecting vacuum artifacts in synthetic audio.

The Physics: A recording of a human in a room will never be truly silent due to
"room tone" (air handling, electronics, reverberation). Natural recordings have
continuous background noise with variance.

The Violation: Deepfakes often use "perfect zeros" (digital silence) between words
or at the very start/end of a clip. The noise floor variance drops to zero or changes
texture instantly between phrases, indicating the audio was generated piecemeal rather
than continuous recording.

Design-Around Strategy: Uses spectral flux and noise floor analysis (NOT Linear Predictive Coding error signal
analysis) to detect perfect mathematical silence and instant texture changes.
"""

import numpy as np
from typing import Dict
from scipy import signal
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

from .base import BaseSensor, SensorResult

# Detection thresholds
MIN_NOISE_FLOOR_VARIANCE = 1e-8  # Minimum variance for natural room tone (dB²)
PERFECT_SILENCE_THRESHOLD_DB = -120.0  # Below this is effectively perfect silence
SPECTRAL_FLUX_CHANGE_THRESHOLD = 0.5  # Instant spectral flux change indicates splicing
MIN_BACKGROUND_ENERGY_DB = -80.0  # Natural recordings have background energy above this
ROOM_TONE_DISTANCE_THRESHOLD = 0.5 # Distance threshold for room tone inconsistency


class DigitalSilenceSensor(BaseSensor):
    """
    Digital Silence sensor that detects vacuum artifacts in synthetic audio.
    
    Analyzes the noise floor between words and detects perfect mathematical silence
    or instant texture changes that indicate piecemeal audio generation rather than
    continuous recording.
    
    Design-Around Strategy:
    - Uses spectral flux and noise floor variance analysis (NOT Linear Predictive Coding error signals)
    - Focuses on acoustic consistency (reverb vs background noise) rather than
      source-filter theory error signals
    """
    
    def __init__(
        self,
        frame_length_ms: float = 25.0,
        hop_length_ms: float = 10.0,
        category: str = "prosecution"
    ):
        """
        Initialize digital silence sensor.
        
        Args:
            frame_length_ms: Frame length for analysis in milliseconds (default: 25ms)
            hop_length_ms: Hop length for analysis in milliseconds (default: 10ms)
            category: "prosecution" or "defense"
        """
        super().__init__("Digital Silence Sensor", category=category)
        self.frame_length_ms = frame_length_ms
        self.hop_length_ms = hop_length_ms
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for digital silence artifacts.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with digital silence analysis
        """
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=None,  # Info-only sensor
                value=0.0,
                threshold=0.5,
                detail="Invalid or empty audio input."
            )
        
        # Skip analysis for very short audio (avoids false positives from zero-padding)
        if len(audio_data) < 2048:
             return SensorResult(
                sensor_name=self.name,
                passed=None, # Abstain/Neutral
                value=0.0,
                threshold=0.5,
                detail="Audio too short for Digital Silence analysis (needs 2048+ samples)."
            )
        
        try:
            # Analyze noise floor and spectral flux
            noise_floor_results = self._analyze_noise_floor(audio_data, samplerate)
            spectral_flux_results = self._analyze_spectral_flux(audio_data, samplerate)
            room_tone_results = self._detect_room_tone_changes(audio_data, samplerate)
            
            # Calculate suspicion score (0-1, higher = more suspicious)
            suspicion_score = 0.0
            violation_count = 0
            
            # Check for perfect silence violations
            if noise_floor_results.get("has_perfect_silence", False):
                suspicion_score += 0.4
                violation_count += noise_floor_results.get("perfect_silence_count", 0)
            
            # Check for zero variance (perfect mathematical silence)
            if noise_floor_results.get("has_zero_variance", False):
                suspicion_score += 0.3
                violation_count += 1
            
            # Check for instant spectral flux changes (splicing artifacts)
            if spectral_flux_results.get("has_instant_change", False):
                suspicion_score += 0.3
                violation_count += spectral_flux_results.get("instant_change_count", 0)
                
            # Check for room tone inconsistencies
            if room_tone_results.get("has_inconsistency", False):
                suspicion_score += 0.3
                violation_count += room_tone_results.get("inconsistency_count", 0)
            
            suspicion_score = min(suspicion_score, 1.0)
            is_suspicious = suspicion_score > 0.5
            
            # Determine passed status (suspicious = failed)
            passed = not is_suspicious if suspicion_score > 0.5 else None
            
            result = SensorResult(
                sensor_name=self.name,
                passed=passed,
                value=round(suspicion_score, 3),
                threshold=0.5,
            )
            
            if is_suspicious:
                result.reason = "DIGITAL_SILENCE_ARTIFACT"
                result.detail = (
                    f"Digital silence artifacts detected. "
                    f"Score: {suspicion_score:.2f} (violations: {violation_count}). "
                    f"Indicates piecemeal audio generation rather than continuous recording."
                )
            else:
                result.detail = (
                    f"Noise floor and spectral flux consistent with natural recording. "
                    f"Score: {suspicion_score:.2f}"
                )
            
            result.metadata = {
                "perfect_silence_count": noise_floor_results.get("perfect_silence_count", 0),
                "has_zero_variance": noise_floor_results.get("has_zero_variance", False),
                "noise_floor_variance": round(noise_floor_results.get("noise_floor_variance", 0.0), 6),
                "min_noise_floor_db": round(noise_floor_results.get("min_noise_floor_db", 0.0), 2),
                "instant_flux_changes": spectral_flux_results.get("instant_change_count", 0),
                "has_instant_change": spectral_flux_results.get("has_instant_change", False),
                "room_tone_inconsistencies": room_tone_results.get("inconsistency_count", 0),
            }
            
            return result
            
        except Exception as e:
            return SensorResult(
                sensor_name=self.name,
                passed=None,
                value=0.0,
                threshold=0.5,
                reason="ERROR",
                detail=f"Digital silence analysis failed: {str(e)}"
            )
    
    def _analyze_noise_floor(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> Dict:
        """
        Analyze noise floor for perfect silence violations.
        
        Args:
            audio: Audio signal
            sr: Sample rate in Hz
            
        Returns:
            Dictionary with noise floor analysis results
        """
        frame_length = int(self.frame_length_ms * sr / 1000.0)
        hop_length = int(self.hop_length_ms * sr / 1000.0)
        
        if len(audio) < frame_length:
            return {
                "has_perfect_silence": False,
                "perfect_silence_count": 0,
                "has_zero_variance": False,
                "noise_floor_variance": 0.0,
                "min_noise_floor_db": 0.0,
            }
        
        # Compute RMS energy in sliding windows
        rms_values = []
        
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]
            rms = float(np.sqrt(np.mean(frame ** 2)))
            # Convert to dB (avoid log(0))
            rms_db = 20 * np.log10(max(rms, 1e-10))
            rms_values.append(rms_db)
        
        if len(rms_values) == 0:
            return {
                "has_perfect_silence": False,
                "perfect_silence_count": 0,
                "has_zero_variance": False,
                "noise_floor_variance": 0.0,
                "min_noise_floor_db": 0.0,
            }
        
        rms_values = np.array(rms_values)
        
        # Check for perfect silence (below threshold)
        perfect_silence_mask = rms_values < PERFECT_SILENCE_THRESHOLD_DB
        perfect_silence_count = int(np.sum(perfect_silence_mask))
        has_perfect_silence = perfect_silence_count > 0
        
        # Check for zero variance (perfect mathematical silence)
        # Natural recordings have variance in noise floor due to room tone
        noise_floor_variance = float(np.var(rms_values))
        has_zero_variance = noise_floor_variance < MIN_NOISE_FLOOR_VARIANCE
        
        # Find minimum noise floor
        min_noise_floor_db = float(np.min(rms_values))
        
        return {
            "has_perfect_silence": has_perfect_silence,
            "perfect_silence_count": perfect_silence_count,
            "has_zero_variance": has_zero_variance,
            "noise_floor_variance": noise_floor_variance,
            "min_noise_floor_db": min_noise_floor_db,
        }
    
    def _analyze_spectral_flux(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> Dict:
        """
        Analyze spectral flux for instant texture changes (splicing artifacts).
        
        Args:
            audio: Audio signal
            sr: Sample rate in Hz
            
        Returns:
            Dictionary with spectral flux analysis results
        """
        frame_length = int(self.frame_length_ms * sr / 1000.0)
        hop_length = int(self.hop_length_ms * sr / 1000.0)
        nperseg = min(frame_length, 1024)
        
        if len(audio) < nperseg * 2:
            return {
                "has_instant_change": False,
                "instant_change_count": 0,
            }
        
        # Compute STFT
        f, t, Zxx = signal.stft(audio, sr, nperseg=nperseg, noverlap=nperseg - hop_length)
        
        # Compute spectral magnitude
        magnitude = np.abs(Zxx)
        
        # Compute spectral flux (rate of change of spectral magnitude)
        # Flux = sum of differences between consecutive frames
        spectral_flux = np.sum(np.diff(magnitude, axis=1) ** 2, axis=0)
        
        # Normalize flux
        if np.max(spectral_flux) > 0:
            spectral_flux = spectral_flux / np.max(spectral_flux)
        
        # Detect instant changes (large flux jumps)
        flux_diff = np.diff(spectral_flux)
        instant_changes = np.abs(flux_diff) > SPECTRAL_FLUX_CHANGE_THRESHOLD
        instant_change_count = int(np.sum(instant_changes))
        has_instant_change = instant_change_count > 0
        
        return {
            "has_instant_change": has_instant_change,
            "instant_change_count": instant_change_count,
        }

    def _detect_room_tone_changes(self, audio: np.ndarray, sr: int) -> Dict:
        """
        Detect inconsistent room tone between segments.
        
        Natural recordings have consistent background noise;
        spliced/generated audio often has room tone discontinuities.
        """
        if not HAS_LIBROSA:
            return {"has_inconsistency": False, "inconsistency_count": 0}

        hop_length = int(self.hop_length_ms * sr / 1000.0)
        
        # Find quiet regions (between speech)
        frame_rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        quiet_threshold = np.percentile(frame_rms, 30)
        quiet_mask = frame_rms < quiet_threshold
        
        # Find contiguous quiet regions
        # Simple run-length encoding style
        quiet_regions = []
        is_quiet = False
        start = 0
        for i, val in enumerate(quiet_mask):
            if val and not is_quiet:
                start = i
                is_quiet = True
            elif not val and is_quiet:
                quiet_regions.append((start, i))
                is_quiet = False
        if is_quiet:
            quiet_regions.append((start, len(quiet_mask)))

        # Analyze spectral characteristics of each quiet region
        room_tones = []
        for start_frame, end_frame in quiet_regions:
            if end_frame - start_frame < 10:  # Skip very short regions
                continue
                
            start_sample = start_frame * hop_length
            end_sample = end_frame * hop_length
            region = audio[start_sample:end_sample]
            
            if len(region) < 2048:
                continue

            # Compute room tone signature (spectral centroid, flatness)
            centroid = np.mean(librosa.feature.spectral_centroid(y=region, sr=sr))
            flatness = np.mean(librosa.feature.spectral_flatness(y=region))
            
            room_tones.append({
                'start_frame': start_frame,
                'centroid': centroid,
                'flatness': flatness
            })
        
        inconsistency_count = 0
        # Compare adjacent room tone signatures
        for i in range(1, len(room_tones)):
            prev = room_tones[i-1]
            curr = room_tones[i]
            
            # Normalize and compare
            # This is a simplified distance metric
            centroid_diff = abs(prev['centroid'] - curr['centroid']) / (prev['centroid'] + 1e-6)
            flatness_diff = abs(prev['flatness'] - curr['flatness']) / (prev['flatness'] + 1e-6)
            
            distance = (centroid_diff + flatness_diff) / 2
            
            if distance > ROOM_TONE_DISTANCE_THRESHOLD:
                inconsistency_count += 1
                
        return {
            "has_inconsistency": inconsistency_count > 0,
            "inconsistency_count": inconsistency_count
        }
