"""
Stage 1: Feature Extraction

Extracts acoustic features from audio for deepfake detection.
"""

import logging
from typing import Dict, Any, Optional, List

import numpy as np
import librosa
from scipy.fftpack import dct

logger = logging.getLogger(__name__)


class FeatureExtractionStage:
    """
    Stage 1: Feature Extraction

    Extracts various acoustic features including:
    - MFCC (Mel-Frequency Cepstral Coefficients)
    - LFCC (Linear Frequency Cepstral Coefficients)
    - CQCC (Constant-Q Cepstral Coefficients)
    - Log-spectrogram
    - Spectral features (centroid, bandwidth, rolloff)
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        n_fft: int = 512,
        hop_length: int = 160,
        win_length: int = 400,
        n_mfcc: int = 20,
        n_lfcc: int = 20,
        feature_types: Optional[List[str]] = None,
        include_deltas: bool = True,
    ):
        """
        Initialize feature extraction stage.

        Args:
            sample_rate: Audio sample rate
            n_fft: FFT size
            hop_length: Hop length in samples
            win_length: Window length in samples
            n_mfcc: Number of MFCCs
            n_lfcc: Number of LFCCs
            feature_types: List of feature types to extract
            include_deltas: Whether to include delta features
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.n_mfcc = n_mfcc
        self.n_lfcc = n_lfcc
        self.feature_types = feature_types or ["mfcc", "lfcc", "logspec"]
        self.include_deltas = include_deltas

        logger.info(f"FeatureExtractionStage initialized: features={self.feature_types}")

    def process(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Extract features from audio.

        Args:
            audio: Input audio array

        Returns:
            Dictionary containing extracted features and metadata
        """
        if audio is None or len(audio) == 0:
            return self._empty_result("Empty audio input")
            
        # Pad audio if shorter than required for analysis (default librosa window is 2048)
        # Even if our n_fft is small (512), other internal calls or defaults might need 2048
        min_len = max(self.n_fft, 2048)
        if len(audio) < min_len:
             padding = min_len - len(audio)
             audio = np.pad(audio, (0, padding), mode='constant')

        try:
            features = {}
            feature_stats = {}

            # Extract each feature type
            for feat_type in self.feature_types:
                feat = self._extract_feature(audio, feat_type)
                if feat is not None:
                    features[feat_type] = feat
                    feature_stats[feat_type] = self._compute_stats(feat)

            # Combine features
            if features:
                combined = self._combine_features(features)
                if self.include_deltas:
                    deltas = self._compute_deltas(combined)
                    delta_deltas = self._compute_delta_deltas(combined)
                    combined_with_deltas = np.concatenate(
                        [combined, deltas, delta_deltas], axis=1
                    )
                else:
                    combined_with_deltas = combined
            else:
                combined_with_deltas = np.array([])

            # Compute anomaly score based on feature statistics
            anomaly_score = self._compute_anomaly_score(feature_stats)

            return {
                "success": True,
                "features": features,
                "combined_features": combined_with_deltas,
                "feature_stats": feature_stats,
                "anomaly_score": float(anomaly_score),
                "num_frames": combined_with_deltas.shape[0] if combined_with_deltas.size > 0 else 0,
                "feature_dim": combined_with_deltas.shape[1] if combined_with_deltas.size > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return self._empty_result(str(e))

    def _extract_feature(self, audio: np.ndarray, feat_type: str) -> Optional[np.ndarray]:
        """Extract a specific feature type."""
        try:
            if feat_type == "mfcc":
                return self._extract_mfcc(audio)
            elif feat_type == "lfcc":
                return self._extract_lfcc(audio)
            elif feat_type == "cqcc":
                return self._extract_cqcc(audio)
            elif feat_type == "logspec":
                return self._extract_logspec(audio)
            elif feat_type == "spectral":
                return self._extract_spectral_features(audio)
            else:
                logger.warning(f"Unknown feature type: {feat_type}")
                return None
        except Exception as e:
            logger.warning(f"Failed to extract {feat_type}: {e}")
            return None

    def _extract_mfcc(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCC features."""
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
        )
        return mfcc.T  # (frames, features)

    def _extract_lfcc(self, audio: np.ndarray) -> np.ndarray:
        """Extract LFCC features."""
        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window="hann",
        )
        magnitude = np.abs(stft)
        log_magnitude = np.log(magnitude + 1e-10)
        lfcc = dct(log_magnitude, axis=0, norm="ortho")[: self.n_lfcc]
        return lfcc.T  # (frames, features)

    def _extract_cqcc(self, audio: np.ndarray, n_bins: int = 84) -> np.ndarray:
        """Extract CQCC features."""
        cqt = librosa.cqt(
            audio,
            sr=self.sample_rate,
            hop_length=self.hop_length,
            n_bins=n_bins,
            bins_per_octave=12,
        )
        magnitude = np.abs(cqt)
        log_magnitude = np.log(magnitude + 1e-10)
        cqcc = dct(log_magnitude, axis=0, norm="ortho")[:20]
        return cqcc.T  # (frames, features)

    def _extract_logspec(self, audio: np.ndarray) -> np.ndarray:
        """Extract log-spectrogram."""
        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window="hann",
        )
        magnitude = np.abs(stft)
        logspec = np.log(magnitude + 1e-10)
        return logspec.T  # (frames, freq_bins)

    def _extract_spectral_features(self, audio: np.ndarray) -> np.ndarray:
        """Extract spectral features (centroid, bandwidth, rolloff)."""
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )
        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )

        features = np.vstack([spectral_centroid, spectral_bandwidth, spectral_rolloff])
        return features.T  # (frames, 3)

    def _combine_features(self, features: Dict[str, np.ndarray]) -> np.ndarray:
        """Combine multiple feature types into single matrix."""
        feature_list = list(features.values())
        if not feature_list:
            return np.array([])

        # Find minimum frame count
        min_frames = min(f.shape[0] for f in feature_list)

        # Trim and concatenate
        trimmed = [f[:min_frames, :] for f in feature_list]
        return np.concatenate(trimmed, axis=1)

    def _compute_deltas(self, features: np.ndarray) -> np.ndarray:
        """Compute delta features."""
        if features.size == 0:
            return features
        return librosa.feature.delta(features.T, order=1).T

    def _compute_delta_deltas(self, features: np.ndarray) -> np.ndarray:
        """Compute delta-delta features."""
        if features.size == 0:
            return features
        return librosa.feature.delta(features.T, order=2).T

    def _compute_stats(self, features: np.ndarray) -> Dict[str, float]:
        """Compute statistics for features."""
        if features.size == 0:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        return {
            "mean": float(np.mean(features)),
            "std": float(np.std(features)),
            "min": float(np.min(features)),
            "max": float(np.max(features)),
        }

    def _compute_anomaly_score(self, feature_stats: Dict[str, Dict[str, float]]) -> float:
        """
        Compute anomaly score based on feature statistics.

        Returns score between 0 (normal) and 1 (anomalous).
        """
        if not feature_stats:
            return 0.5

        # Simple heuristic based on feature variance
        scores = []
        for stats in feature_stats.values():
            # Normalize std to [0, 1] range
            normalized_std = min(stats.get("std", 0.0) / 10.0, 1.0)
            scores.append(normalized_std)

        return float(np.mean(scores)) if scores else 0.5

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed extraction."""
        return {
            "success": False,
            "error": error_msg,
            "features": {},
            "combined_features": np.array([]),
            "feature_stats": {},
            "anomaly_score": 0.5,
            "num_frames": 0,
            "feature_dim": 0,
        }
