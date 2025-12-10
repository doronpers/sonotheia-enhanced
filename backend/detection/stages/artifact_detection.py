"""
Stage 3: Artifact Detection

Detects audio artifacts indicative of manipulation or synthesis.
"""

import logging
from typing import Dict, Any, List

import numpy as np
from scipy import signal
from scipy.stats import kurtosis, skew

logger = logging.getLogger(__name__)


class ArtifactDetectionStage:
    """
    Stage 3: Artifact Detection

    Detects various audio artifacts:
    - Clicks and pops
    - Silence patterns
    - Frequency artifacts
    - Codec artifacts
    - Phase inconsistencies
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold_db: float = -40.0,
        min_silence_duration: float = 0.1,
        click_threshold: float = 0.8,
        click_min_gap: int = 100,
    ):
        """
        Initialize artifact detection stage.

        Args:
            sample_rate: Audio sample rate
            silence_threshold_db: Threshold for silence detection
            min_silence_duration: Minimum silence duration in seconds
            click_threshold: Threshold for click detection
            click_min_gap: Minimum gap between clicks in samples
        """
        self.sample_rate = sample_rate
        self.silence_threshold_db = silence_threshold_db
        self.min_silence_duration = min_silence_duration
        self.click_threshold = click_threshold
        self.click_min_gap = click_min_gap

        logger.info("ArtifactDetectionStage initialized")

    def process(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Detect artifacts in audio.

        Args:
            audio: Input audio array

        Returns:
            Dictionary containing artifact detection results
        """
        if audio is None or len(audio) == 0:
            return self._empty_result("Empty audio input")

        try:
            # Detect different artifact types
            silence_artifacts = self._detect_silence_patterns(audio)
            click_artifacts = self._detect_clicks(audio)
            frequency_artifacts = self._detect_frequency_artifacts(audio)
            phase_artifacts = self._detect_phase_artifacts(audio)
            statistical_artifacts = self._compute_statistical_features(audio)

            # Compute overall artifact score
            artifact_score = self._compute_artifact_score(
                silence_artifacts,
                click_artifacts,
                frequency_artifacts,
                phase_artifacts,
                statistical_artifacts,
            )

            # Compile artifact summary
            all_artifacts = self._compile_artifacts(
                silence_artifacts,
                click_artifacts,
                frequency_artifacts,
                phase_artifacts,
            )

            return {
                "success": True,
                "artifact_score": float(artifact_score),
                "silence_artifacts": silence_artifacts,
                "click_artifacts": click_artifacts,
                "frequency_artifacts": frequency_artifacts,
                "phase_artifacts": phase_artifacts,
                "statistical_features": statistical_artifacts,
                "all_artifacts": all_artifacts,
                "total_artifacts": len(all_artifacts),
            }

        except Exception as e:
            logger.error(f"Artifact detection failed: {e}")
            return self._empty_result(str(e))

    def _detect_silence_patterns(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detect unusual silence patterns."""
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)

        # Compute frame energies in dB
        energies = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i : i + frame_length]
            energy = np.sqrt(np.mean(frame ** 2))
            energy_db = 20 * np.log10(energy + 1e-10)
            energies.append(energy_db)

        energies = np.array(energies)

        # Find silence regions
        silence_mask = energies < self.silence_threshold_db
        silence_regions = self._find_regions(silence_mask, hop_length)

        # Filter by minimum duration
        min_samples = int(self.min_silence_duration * self.sample_rate / hop_length)
        silence_regions = [
            r for r in silence_regions if r["duration_frames"] >= min_samples
        ]

        return {
            "num_silence_regions": len(silence_regions),
            "total_silence_duration": sum(
                r["duration_frames"] * hop_length / self.sample_rate
                for r in silence_regions
            ),
            "regions": silence_regions,
            "suspicious": len(silence_regions) > 5,  # Heuristic
        }

    def _detect_clicks(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detect clicks and pops in audio."""
        # Compute local maxima in derivative
        audio_diff = np.abs(np.diff(audio))

        # Normalize
        if np.max(audio_diff) > 0:
            audio_diff = audio_diff / np.max(audio_diff)

        # Find peaks above threshold
        peaks, _ = signal.find_peaks(
            audio_diff,
            height=self.click_threshold,
            distance=self.click_min_gap,
        )

        click_times = peaks / self.sample_rate

        return {
            "num_clicks": len(peaks),
            "click_times": click_times.tolist(),
            "click_magnitudes": audio_diff[peaks].tolist() if len(peaks) > 0 else [],
            "suspicious": len(peaks) > 10,  # Heuristic
        }

    def _detect_frequency_artifacts(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detect frequency domain artifacts."""
        # Compute spectrum
        # Compute spectrum
        n_fft = 2048
        if len(audio) < n_fft:
            return {
                "spectral_flatness": 1.0, # Neutral
                "spectral_peak_ratio": 0.0,
                "num_spectral_holes": 0,
                "high_frequency_energy": 0.0,
                "suspicious": False,
                "note": "Audio too short for frequency analysis"
            }
            
        spectrum = np.abs(np.fft.rfft(audio, n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, 1 / self.sample_rate)

        # Check for unusual spectral characteristics
        spectral_flatness = self._compute_spectral_flatness(spectrum)
        spectral_peak_ratio = self._compute_peak_ratio(spectrum)

        # Detect spectral holes (frequencies with unusually low energy)
        spectrum_db = 20 * np.log10(spectrum + 1e-10)
        mean_db = np.mean(spectrum_db)
        std_db = np.std(spectrum_db)
        hole_indices = np.where(spectrum_db < mean_db - 3 * std_db)[0]

        # Check for aliasing artifacts
        nyquist = self.sample_rate / 2
        high_freq_indices = np.where(freqs > nyquist * 0.9)[0]
        high_freq_energy = np.mean(spectrum[high_freq_indices]) if len(high_freq_indices) > 0 else 0

        return {
            "spectral_flatness": float(spectral_flatness),
            "spectral_peak_ratio": float(spectral_peak_ratio),
            "num_spectral_holes": len(hole_indices),
            "high_frequency_energy": float(high_freq_energy),
            "suspicious": spectral_flatness > 0.9 or len(hole_indices) > 50,
        }

    def _detect_phase_artifacts(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detect phase inconsistencies."""
        n_fft = 2048
        hop_length = n_fft // 4

        # Compute STFT
        num_frames = (len(audio) - n_fft) // hop_length + 1
        if num_frames < 2:
            return {"phase_variance": 0.0, "phase_jumps": 0, "suspicious": False}

        phases = []
        for i in range(num_frames):
            start = i * hop_length
            frame = audio[start : start + n_fft]
            if len(frame) < n_fft:
                break
            spectrum = np.fft.rfft(frame)
            phase = np.angle(spectrum)
            phases.append(phase)

        phases = np.array(phases)

        # Compute phase derivatives
        phase_diff = np.diff(phases, axis=0)
        phase_diff = np.angle(np.exp(1j * phase_diff))  # Wrap to [-pi, pi]

        # Detect phase jumps
        phase_jump_threshold = np.pi / 2
        phase_jumps = np.sum(np.abs(phase_diff) > phase_jump_threshold)

        phase_variance = float(np.var(phase_diff))

        return {
            "phase_variance": phase_variance,
            "phase_jumps": int(phase_jumps),
            "suspicious": phase_jumps > 100,
        }

    def _compute_statistical_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Compute statistical features of audio."""
        return {
            "mean": float(np.mean(audio)),
            "std": float(np.std(audio)),
            "kurtosis": float(kurtosis(audio)),
            "skewness": float(skew(audio)),
            "zero_crossing_rate": float(
                np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
            ),
            "rms": float(np.sqrt(np.mean(audio ** 2))),
        }

    def _compute_spectral_flatness(self, spectrum: np.ndarray) -> float:
        """Compute spectral flatness (Wiener entropy)."""
        spectrum = spectrum + 1e-10
        geometric_mean = np.exp(np.mean(np.log(spectrum)))
        arithmetic_mean = np.mean(spectrum)
        return float(geometric_mean / arithmetic_mean)

    def _compute_peak_ratio(self, spectrum: np.ndarray) -> float:
        """Compute ratio of peak to mean energy."""
        if np.mean(spectrum) == 0:
            return 0.0
        return float(np.max(spectrum) / np.mean(spectrum))

    def _find_regions(self, mask: np.ndarray, hop_length: int) -> List[Dict[str, Any]]:
        """Find continuous regions in boolean mask."""
        regions = []
        in_region = False
        start_idx = 0

        for i, val in enumerate(mask):
            if val and not in_region:
                in_region = True
                start_idx = i
            elif not val and in_region:
                in_region = False
                regions.append({
                    "start_frame": start_idx,
                    "end_frame": i,
                    "duration_frames": i - start_idx,
                    "start_time": float(start_idx * hop_length / self.sample_rate),
                    "end_time": float(i * hop_length / self.sample_rate),
                })

        if in_region:
            regions.append({
                "start_frame": start_idx,
                "end_frame": len(mask),
                "duration_frames": len(mask) - start_idx,
                "start_time": float(start_idx * hop_length / self.sample_rate),
                "end_time": float(len(mask) * hop_length / self.sample_rate),
            })

        return regions

    def _compute_artifact_score(
        self,
        silence: Dict[str, Any],
        clicks: Dict[str, Any],
        frequency: Dict[str, Any],
        phase: Dict[str, Any],
        stats: Dict[str, Any],
    ) -> float:
        """Compute overall artifact score."""
        scores = []

        # Silence score
        if silence.get("suspicious", False):
            scores.append(0.3)
        else:
            scores.append(min(silence.get("num_silence_regions", 0) / 10.0, 0.3))

        # Click score
        if clicks.get("suspicious", False):
            scores.append(0.3)
        else:
            scores.append(min(clicks.get("num_clicks", 0) / 20.0, 0.3))

        # Frequency score
        if frequency.get("suspicious", False):
            scores.append(0.2)
        else:
            scores.append(min(frequency.get("num_spectral_holes", 0) / 100.0, 0.2))

        # Phase score
        if phase.get("suspicious", False):
            scores.append(0.2)
        else:
            scores.append(min(phase.get("phase_jumps", 0) / 200.0, 0.2))

        return sum(scores)

    def _compile_artifacts(
        self,
        silence: Dict[str, Any],
        clicks: Dict[str, Any],
        frequency: Dict[str, Any],
        phase: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Compile all artifacts into unified list."""
        artifacts = []

        # Add silence artifacts
        for region in silence.get("regions", []):
            artifacts.append({
                "type": "silence",
                "start_time": region["start_time"],
                "end_time": region["end_time"],
                "severity": "medium",
            })

        # Add click artifacts
        for i, time in enumerate(clicks.get("click_times", [])):
            mag = clicks.get("click_magnitudes", [0.5])[i] if i < len(clicks.get("click_magnitudes", [])) else 0.5
            artifacts.append({
                "type": "click",
                "time": float(time),
                "magnitude": float(mag),
                "severity": "high" if mag > 0.9 else "medium",
            })

        return artifacts

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed detection."""
        return {
            "success": False,
            "error": error_msg,
            "artifact_score": 0.5,
            "silence_artifacts": {},
            "click_artifacts": {},
            "frequency_artifacts": {},
            "phase_artifacts": {},
            "statistical_features": {},
            "all_artifacts": [],
            "total_artifacts": 0,
        }
