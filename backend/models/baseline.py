"""
Baseline Spoof Detection Model

Implements a GMM-based classifier for audio deepfake detection.
"""

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
import pickle
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class GMMSpoofDetector:
    """GMM-based spoof detector"""

    def __init__(self, n_components: int = 32, random_state: int = 42):
        """
        Initialize GMM spoof detector

        Args:
            n_components: Number of Gaussian components
            random_state: Random seed for reproducibility
        """
        self.n_components = n_components
        self.random_state = random_state

        # Create two GMMs: one for genuine, one for spoof
        self.gmm_genuine = GaussianMixture(
            n_components=n_components,
            covariance_type='diag',
            random_state=random_state,
            max_iter=100
        )

        self.gmm_spoof = GaussianMixture(
            n_components=n_components,
            covariance_type='diag',
            random_state=random_state,
            max_iter=100
        )

        self.scaler = StandardScaler()
        self.is_trained = False

    def train(self, genuine_features: np.ndarray, spoof_features: np.ndarray):
        """
        Train GMMs on genuine and spoof features

        Args:
            genuine_features: Features from genuine audio (samples x features)
            spoof_features: Features from spoof audio (samples x features)
        """
        logger.info("Training GMM spoof detector...")
        logger.info(f"Genuine samples: {genuine_features.shape[0]}, Spoof samples: {spoof_features.shape[0]}")

        # Fit scaler on all data
        all_features = np.vstack([genuine_features, spoof_features])
        self.scaler.fit(all_features)

        # Normalize features
        genuine_norm = self.scaler.transform(genuine_features)
        spoof_norm = self.scaler.transform(spoof_features)

        # Train GMMs
        logger.info("Training genuine GMM...")
        self.gmm_genuine.fit(genuine_norm)

        logger.info("Training spoof GMM...")
        self.gmm_spoof.fit(spoof_norm)

        self.is_trained = True
        logger.info("Training complete!")

    def predict_score(self, features: np.ndarray) -> float:
        """
        Predict spoof score for audio features

        Args:
            features: Audio features (frames x features)

        Returns:
            Spoof score in [0, 1] where higher = more likely spoof
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first or load a trained model.")

        # Normalize features
        features_norm = self.scaler.transform(features)

        # Compute log-likelihoods
        ll_genuine = self.gmm_genuine.score_samples(features_norm)
        ll_spoof = self.gmm_spoof.score_samples(features_norm)

        # Average across frames
        avg_ll_genuine = np.mean(ll_genuine)
        avg_ll_spoof = np.mean(ll_spoof)

        # Compute score using likelihood ratio
        # Convert to probability using sigmoid-like function
        score = 1.0 / (1.0 + np.exp(avg_ll_genuine - avg_ll_spoof))

        return float(score)

    def predict_batch(self, features_list: list) -> np.ndarray:
        """
        Predict spoof scores for batch of feature matrices

        Args:
            features_list: List of feature matrices

        Returns:
            Array of spoof scores
        """
        scores = []
        for features in features_list:
            score = self.predict_score(features)
            scores.append(score)

        return np.array(scores)

    def save(self, model_path: str):
        """
        Save trained model

        Args:
            model_path: Path to save model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        model_data = {
            'gmm_genuine': self.gmm_genuine,
            'gmm_spoof': self.gmm_spoof,
            'scaler': self.scaler,
            'n_components': self.n_components,
            'random_state': self.random_state,
            'is_trained': self.is_trained
        }

        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {model_path}")

    def load(self, model_path: str):
        """
        Load trained model

        Args:
            model_path: Path to model file
        """
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.gmm_genuine = model_data['gmm_genuine']
        self.gmm_spoof = model_data['gmm_spoof']
        self.scaler = model_data['scaler']
        self.n_components = model_data['n_components']
        self.random_state = model_data['random_state']
        self.is_trained = model_data['is_trained']

        logger.info(f"Model loaded from {model_path}")


class SimpleCNNSpoofDetector:
    """
    Simple CNN-based spoof detector (PyTorch)

    This is a placeholder for future CNN implementation.
    For MVP, we use GMM which doesn't require large datasets.
    """

    def __init__(self):
        logger.warning("SimpleCNNSpoofDetector is not implemented in MVP. Use GMMSpoofDetector instead.")
        raise NotImplementedError("CNN detector not implemented in MVP. Use GMMSpoofDetector.")


# Convenience function
def predict_spoof_score(features: np.ndarray, model_path: Optional[str] = None) -> float:
    """
    Predict spoof score using default or loaded model

    Args:
        features: Audio features (frames x features)
        model_path: Optional path to trained model

    Returns:
        Spoof score in [0, 1]
    """
    detector = GMMSpoofDetector()

    if model_path and Path(model_path).exists():
        detector.load(model_path)
    else:
        # Return placeholder score if no model available
        logger.warning("No trained model found, returning placeholder score")
        return 0.5

    return detector.predict_score(features)
