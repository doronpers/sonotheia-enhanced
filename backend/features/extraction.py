"""
Feature Extraction Module

Implements CQCC, LFCC, and log-spectrogram features for audio deepfake detection.
"""

import numpy as np
import librosa
from scipy.fftpack import dct
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract acoustic features from audio"""

    def __init__(self, sr: int = 16000, n_fft: int = 512, hop_length: int = 160, win_length: int = 400):
        """
        Initialize feature extractor

        Args:
            sr: Sample rate (default 16kHz)
            n_fft: FFT size
            hop_length: Hop length in samples (10ms at 16kHz)
            win_length: Window length in samples (25ms at 16kHz)
        """
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length

    def extract_lfcc(self, audio: np.ndarray, n_lfcc: int = 20) -> np.ndarray:
        """
        Extract Linear Frequency Cepstral Coefficients (LFCC)

        Args:
            audio: Input audio array
            n_lfcc: Number of LFCCs to extract

        Returns:
            LFCC matrix (frames x n_lfcc)
        """
        # Compute STFT
        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window='hann'
        )

        # Magnitude spectrum
        magnitude = np.abs(stft)

        # Log magnitude
        log_magnitude = np.log(magnitude + 1e-10)

        # Apply DCT (Discrete Cosine Transform)
        lfcc = dct(log_magnitude, axis=0, norm='ortho')[:n_lfcc]

        # Transpose to (frames, features)
        lfcc = lfcc.T

        logger.debug(f"Extracted LFCC: shape={lfcc.shape}")

        return lfcc

    def extract_logspec(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract log-magnitude spectrogram

        Args:
            audio: Input audio array

        Returns:
            Log-spectrogram matrix (frames x freq_bins)
        """
        # Compute STFT
        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window='hann'
        )

        # Log magnitude spectrogram
        magnitude = np.abs(stft)
        logspec = np.log(magnitude + 1e-10)

        # Transpose to (frames, freq_bins)
        logspec = logspec.T

        logger.debug(f"Extracted log-spectrogram: shape={logspec.shape}")

        return logspec

    def extract_cqcc(self, audio: np.ndarray, n_cqcc: int = 20, n_bins: int = 84) -> np.ndarray:
        """
        Extract Constant-Q Cepstral Coefficients (CQCC)

        Args:
            audio: Input audio array
            n_cqcc: Number of CQCCs to extract
            n_bins: Number of frequency bins in CQT (default 84 for 16kHz sr)

        Returns:
            CQCC matrix (frames x n_cqcc)
        """
        # Compute Constant-Q Transform
        # Use 84 bins to avoid exceeding Nyquist frequency at 16kHz
        cqt = librosa.cqt(
            audio,
            sr=self.sr,
            hop_length=self.hop_length,
            n_bins=n_bins,
            bins_per_octave=12
        )

        # Magnitude
        magnitude = np.abs(cqt)

        # Log magnitude
        log_magnitude = np.log(magnitude + 1e-10)

        # Apply DCT
        cqcc = dct(log_magnitude, axis=0, norm='ortho')[:n_cqcc]

        # Transpose to (frames, features)
        cqcc = cqcc.T

        logger.debug(f"Extracted CQCC: shape={cqcc.shape}")

        return cqcc

    def extract_mfcc(self, audio: np.ndarray, n_mfcc: int = 20) -> np.ndarray:
        """
        Extract Mel-Frequency Cepstral Coefficients (MFCC) as reference

        Args:
            audio: Input audio array
            n_mfcc: Number of MFCCs to extract

        Returns:
            MFCC matrix (frames x n_mfcc)
        """
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=self.sr,
            n_mfcc=n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length
        )

        # Transpose to (frames, features)
        mfcc = mfcc.T

        logger.debug(f"Extracted MFCC: shape={mfcc.shape}")

        return mfcc

    def extract_feature_stack(self, audio: np.ndarray, feature_types: list = ['lfcc', 'logspec']) -> np.ndarray:
        """
        Extract and concatenate multiple feature types

        Args:
            audio: Input audio array
            feature_types: List of feature types to extract ('lfcc', 'cqcc', 'logspec', 'mfcc')

        Returns:
            Concatenated feature matrix (frames x total_dims)
        """
        features = []

        for feat_type in feature_types:
            if feat_type == 'lfcc':
                feat = self.extract_lfcc(audio)
            elif feat_type == 'cqcc':
                feat = self.extract_cqcc(audio)
            elif feat_type == 'logspec':
                feat = self.extract_logspec(audio)
            elif feat_type == 'mfcc':
                feat = self.extract_mfcc(audio)
            else:
                raise ValueError(f"Unknown feature type: {feat_type}")

            features.append(feat)

        # Find minimum number of frames (features may have slightly different lengths)
        min_frames = min(f.shape[0] for f in features)

        # Trim all features to same length
        features = [f[:min_frames, :] for f in features]

        # Concatenate along feature dimension
        feature_stack = np.concatenate(features, axis=1)

        logger.info(f"Extracted feature stack: shape={feature_stack.shape}, types={feature_types}")

        return feature_stack

    def compute_deltas(self, features: np.ndarray) -> np.ndarray:
        """
        Compute delta (first-order derivative) features

        Args:
            features: Input feature matrix (frames x features)

        Returns:
            Delta features
        """
        deltas = librosa.feature.delta(features.T, order=1)
        return deltas.T

    def compute_delta_deltas(self, features: np.ndarray) -> np.ndarray:
        """
        Compute delta-delta (second-order derivative) features

        Args:
            features: Input feature matrix (frames x features)

        Returns:
            Delta-delta features
        """
        delta_deltas = librosa.feature.delta(features.T, order=2)
        return delta_deltas.T

    def extract_with_deltas(self, audio: np.ndarray, feature_types: list = ['lfcc']) -> np.ndarray:
        """
        Extract features with delta and delta-delta

        Args:
            audio: Input audio array
            feature_types: List of feature types

        Returns:
            Feature matrix with deltas (frames x (features + deltas + delta_deltas))
        """
        # Extract base features
        features = self.extract_feature_stack(audio, feature_types)

        # Compute deltas
        deltas = self.compute_deltas(features)
        delta_deltas = self.compute_delta_deltas(features)

        # Concatenate
        features_with_deltas = np.concatenate([features, deltas, delta_deltas], axis=1)

        logger.info(f"Extracted features with deltas: shape={features_with_deltas.shape}")

        return features_with_deltas


# Convenience functions
def extract_lfcc(audio: np.ndarray, sr: int = 16000, n_lfcc: int = 20) -> np.ndarray:
    """Extract LFCC features"""
    extractor = FeatureExtractor(sr=sr)
    return extractor.extract_lfcc(audio, n_lfcc=n_lfcc)


def extract_cqcc(audio: np.ndarray, sr: int = 16000, n_cqcc: int = 20) -> np.ndarray:
    """Extract CQCC features"""
    extractor = FeatureExtractor(sr=sr)
    return extractor.extract_cqcc(audio, n_cqcc=n_cqcc)


def extract_logspec(audio: np.ndarray, sr: int = 16000) -> np.ndarray:
    """Extract log-spectrogram features"""
    extractor = FeatureExtractor(sr=sr)
    return extractor.extract_logspec(audio)


def extract_feature_stack(audio: np.ndarray, sr: int = 16000, feature_types: list = ['lfcc', 'logspec']) -> np.ndarray:
    """Extract and stack multiple features"""
    extractor = FeatureExtractor(sr=sr)
    return extractor.extract_feature_stack(audio, feature_types=feature_types)
