"""
Stage 2: Temporal Analysis

Analyzes temporal patterns in audio to detect deepfake artifacts.
"""

import logging
from typing import Dict, Any, List, Optional

import numpy as np
from scipy.stats import zscore

logger = logging.getLogger(__name__)


class TemporalAnalysisStage:
    """
    Stage 2: Temporal Analysis

    Detects temporal artifacts and inconsistencies:
    - Segment-level anomalies
    - Temporal discontinuities
    - Energy envelope patterns
    - Transition artifacts
    """

    def __init__(
        self,
        window_size: int = 100,
        hop_size: int = 50,
        min_segment_length: int = 10,
        smoothing_window: int = 5,
        threshold_std_multiplier: float = 2.0,
        sample_rate: int = 16000,
    ):
        """
        Initialize temporal analysis stage.

        Args:
            window_size: Analysis window size in frames
            hop_size: Hop size in frames
            min_segment_length: Minimum segment length for analysis
            smoothing_window: Smoothing window size
            threshold_std_multiplier: Multiplier for anomaly threshold
            sample_rate: Audio sample rate
        """
        self.window_size = window_size
        self.hop_size = hop_size
        self.min_segment_length = min_segment_length
        self.smoothing_window = smoothing_window
        self.threshold_std_multiplier = threshold_std_multiplier
        self.sample_rate = sample_rate

        logger.info(f"TemporalAnalysisStage initialized: window={window_size}")

    def process(
        self, audio: np.ndarray, features: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Analyze temporal patterns in audio.

        Args:
            audio: Input audio array
            features: Optional pre-extracted features

        Returns:
            Dictionary containing temporal analysis results
        """
        if audio is None or len(audio) == 0:
            return self._empty_result("Empty audio input")

        try:
            # Compute energy envelope
            energy_envelope = self._compute_energy_envelope(audio)

            # Detect temporal discontinuities
            discontinuities = self._detect_discontinuities(audio)

            # Analyze segment transitions
            transitions = self._analyze_transitions(audio)

            # Detect temporal anomalies in features if provided
            if features is not None and features.size > 0:
                feature_anomalies = self._detect_feature_anomalies(features)
            else:
                feature_anomalies = {"anomaly_frames": [], "scores": []}

            # Compute overall temporal score
            temporal_score = self._compute_temporal_score(
                discontinuities, transitions, feature_anomalies
            )

            # Identify suspicious segments
            suspicious_segments = self._identify_suspicious_segments(
                audio, discontinuities, temporal_score
            )

            return {
                "success": True,
                "temporal_score": float(temporal_score),
                "energy_envelope": energy_envelope.tolist(),
                "discontinuities": discontinuities,
                "transitions": transitions,
                "feature_anomalies": feature_anomalies,
                "suspicious_segments": suspicious_segments,
                "num_anomalies": len(discontinuities.get("positions", [])),
            }

        except Exception as e:
            logger.error(f"Temporal analysis failed: {e}")
            return self._empty_result(str(e))

    def _compute_energy_envelope(self, audio: np.ndarray) -> np.ndarray:
        """Compute energy envelope of audio."""
        frame_length = int(0.025 * self.sample_rate)  # 25ms
        hop_length = int(0.010 * self.sample_rate)  # 10ms

        # Compute RMS energy
        energy = np.array([
            np.sqrt(np.mean(audio[i : i + frame_length] ** 2))
            for i in range(0, len(audio) - frame_length, hop_length)
        ])

        # Smooth the envelope
        if len(energy) > self.smoothing_window:
            kernel = np.ones(self.smoothing_window) / self.smoothing_window
            energy = np.convolve(energy, kernel, mode="same")

        return energy

    def _detect_discontinuities(self, audio: np.ndarray) -> Dict[str, Any]:
        """Detect temporal discontinuities in audio."""
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)

        # Compute frame-wise differences
        diffs = []
        for i in range(hop_length, len(audio) - frame_length, hop_length):
            prev_frame = audio[i - hop_length : i - hop_length + frame_length]
            curr_frame = audio[i : i + frame_length]
            diff = np.mean(np.abs(curr_frame - prev_frame))
            diffs.append(diff)

        diffs = np.array(diffs)
        if len(diffs) == 0:
            return {"positions": [], "magnitudes": [], "threshold": 0.0}

        # Detect anomalies using z-score
        z_scores = zscore(diffs) if np.std(diffs) > 0 else np.zeros_like(diffs)
        threshold = self.threshold_std_multiplier

        anomaly_indices = np.where(np.abs(z_scores) > threshold)[0]
        anomaly_times = anomaly_indices * hop_length / self.sample_rate

        return {
            "positions": anomaly_times.tolist(),
            "magnitudes": diffs[anomaly_indices].tolist() if len(anomaly_indices) > 0 else [],
            "threshold": float(threshold),
            "z_scores": z_scores.tolist(),
        }

    def _analyze_transitions(self, audio: np.ndarray) -> Dict[str, Any]:
        """Analyze segment transitions for artifacts."""
        # Compute spectral flux
        n_fft = 512

        # Simple spectral flux computation
        spec = np.abs(np.fft.rfft(audio[: len(audio) // n_fft * n_fft].reshape(-1, n_fft)))
        spectral_flux = np.sum(np.diff(spec, axis=0) ** 2, axis=1)

        if len(spectral_flux) == 0:
            return {"flux_mean": 0.0, "flux_std": 0.0, "transition_points": []}

        # Detect transition points
        flux_z = zscore(spectral_flux) if np.std(spectral_flux) > 0 else np.zeros_like(spectral_flux)
        transition_indices = np.where(flux_z > self.threshold_std_multiplier)[0]

        return {
            "flux_mean": float(np.mean(spectral_flux)),
            "flux_std": float(np.std(spectral_flux)),
            "transition_points": transition_indices.tolist(),
            "num_transitions": len(transition_indices),
        }

    def _detect_feature_anomalies(self, features: np.ndarray) -> Dict[str, Any]:
        """Detect anomalies in feature sequences."""
        if features.ndim == 1:
            features = features.reshape(-1, 1)

        # Compute frame-wise anomaly scores
        feature_mean = np.mean(features, axis=0)
        feature_std = np.std(features, axis=0) + 1e-10

        z_scores = np.abs((features - feature_mean) / feature_std)
        frame_scores = np.mean(z_scores, axis=1)

        # Identify anomalous frames
        threshold = self.threshold_std_multiplier
        anomaly_frames = np.where(frame_scores > threshold)[0]

        return {
            "anomaly_frames": anomaly_frames.tolist(),
            "scores": frame_scores.tolist(),
            "threshold": float(threshold),
            "num_anomalies": len(anomaly_frames),
        }

    def _compute_temporal_score(
        self,
        discontinuities: Dict[str, Any],
        transitions: Dict[str, Any],
        feature_anomalies: Dict[str, Any],
    ) -> float:
        """Compute overall temporal anomaly score."""
        scores = []

        # Score from discontinuities
        num_disc = len(discontinuities.get("positions", []))
        disc_score = min(num_disc / 10.0, 1.0)  # Normalize
        scores.append(disc_score * 0.4)

        # Score from transitions
        num_trans = transitions.get("num_transitions", 0)
        trans_score = min(num_trans / 20.0, 1.0)
        scores.append(trans_score * 0.3)

        # Score from feature anomalies
        num_feat_anom = feature_anomalies.get("num_anomalies", 0)
        feat_score = min(num_feat_anom / 50.0, 1.0)
        scores.append(feat_score * 0.3)

        return sum(scores)

    def _identify_suspicious_segments(
        self,
        audio: np.ndarray,
        discontinuities: Dict[str, Any],
        temporal_score: float,
    ) -> List[Dict[str, Any]]:
        """Identify suspicious time segments."""
        segments = []
        positions = discontinuities.get("positions", [])
        magnitudes = discontinuities.get("magnitudes", [])

        for i, (pos, mag) in enumerate(zip(positions, magnitudes)):
            segment = {
                "start_time": float(max(0, pos - 0.1)),
                "end_time": float(min(len(audio) / self.sample_rate, pos + 0.1)),
                "confidence": float(min(mag * 10, 1.0)),
                "type": "discontinuity",
            }
            segments.append(segment)

        return segments

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed analysis."""
        return {
            "success": False,
            "error": error_msg,
            "temporal_score": 0.5,
            "energy_envelope": [],
            "discontinuities": {"positions": [], "magnitudes": []},
            "transitions": {},
            "feature_anomalies": {},
            "suspicious_segments": [],
            "num_anomalies": 0,
        }
