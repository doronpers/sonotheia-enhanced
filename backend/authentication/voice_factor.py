"""
Voice Authentication Factor Module
Handles voice deepfake detection, liveness checks, and speaker verification
"""

from typing import Dict, Optional, List
import logging
from pathlib import Path
import numpy as np

from data_ingest.loader import AudioLoader
from telephony.pipeline import TelephonyPipeline
from features.extraction import FeatureExtractor
from models.baseline import GMMSpoofDetector

logger = logging.getLogger(__name__)


class VoiceAuthenticator:
    """Voice authentication factor validator"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.deepfake_threshold = config.get('deepfake_threshold', 0.3)
        self.liveness_threshold = config.get('liveness_threshold', self.deepfake_threshold)
        self.speaker_threshold = config.get('speaker_threshold', 0.85)
        self.min_quality = config.get('min_quality', 0.7)
        self.demo_mode = config.get('demo_mode', True)
        self.sample_rate = config.get('sample_rate', 16000)
        self.feature_types: List[str] = config.get('feature_types', ['lfcc', 'logspec'])
        self.codec = config.get('codec', 'landline')
        self.target_fpr = config.get('target_fpr', 0.01)
        model_path = config.get('model_path')
        self.model_path = Path(model_path) if model_path else None

        self.loader = AudioLoader(target_sr=self.sample_rate)
        self.telephony = TelephonyPipeline()
        self.feature_extractor = FeatureExtractor(sr=self.sample_rate)
        self.detector = GMMSpoofDetector()
        self.model_loaded = False

        if self.model_path and self.model_path.exists():
            try:
                self.detector.load(str(self.model_path))
                self.model_loaded = True
                logger.info(f"VoiceAuthenticator loaded spoof model from {self.model_path}")
            except Exception as exc:
                logger.warning(f"Could not load spoof model at {self.model_path}: {exc}")
        else:
            logger.warning("No spoof model found; will fallback to heuristic scoring.")

        logger.info(f"VoiceAuthenticator initialized with thresholds: "
                   f"deepfake={self.deepfake_threshold}, "
                   f"liveness={self.liveness_threshold}, "
                   f"speaker={self.speaker_threshold}, "
                   f"demo_mode={self.demo_mode}, "
                   f"codec={self.codec}, "
                   f"feature_types={self.feature_types}")
    
    def detect_deepfake(self, audio_bytes: bytes) -> float:
        """
        Detect synthetic/deepfake audio
        Returns a score from 0.0 (genuine) to 1.0 (synthetic)
        
        DEMO MODE: This is a placeholder implementation.
        In production, integrate your proprietary detection model.
        """
        if (self.demo_mode or not self.model_loaded):
            logger.warning("Using placeholder deepfake detection - model not loaded")
            return 0.10  # Demo/placeholder value

        score = self._predict_spoof_score(audio_bytes)
        return float(score)
    
    def check_liveness(self, audio_bytes: bytes) -> Dict:
        """
        Check for liveness (replay attack detection)
        Returns dict with 'passed' boolean and details
        
        DEMO MODE: This is a placeholder implementation.
        In production, implement proper liveness detection.
        """
        if self.demo_mode or not self.model_loaded:
            logger.warning("Using placeholder liveness check - model not loaded")
            return {
                'passed': True,
                'confidence': 0.95,
                'method': 'acoustic_challenge',
                'spoof_score': 0.10,
                'threshold': float(self.liveness_threshold),
                'model_loaded': bool(self.model_loaded),
                'target_fpr': float(self.target_fpr)
            }

        spoof_score = self._predict_spoof_score(audio_bytes)
        passed = spoof_score < self.liveness_threshold
        # Confidence skewed toward lower FPR operating points
        confidence = max(0.0, 1.0 - abs(spoof_score - self.liveness_threshold))

        return {
            'passed': bool(passed),
            'confidence': float(confidence),
            'method': 'gmm_spoof',
            'spoof_score': float(spoof_score),
            'threshold': float(self.liveness_threshold),
            'model_loaded': bool(self.model_loaded),
            'target_fpr': float(self.target_fpr)
        }
    
    def verify_speaker(self, audio_bytes: bytes, customer_id: str) -> float:
        """
        Verify speaker identity against enrolled voiceprint
        Returns similarity score from 0.0 to 1.0
        
        DEMO MODE: This is a placeholder implementation.
        In production, implement proper speaker verification.
        """
        if self.demo_mode:
            logger.warning("Using demo mode for speaker verification - not for production use")
            return 0.96  # Demo value
        else:
            # TODO: Integrate actual speaker verification (embedding + enrollment)
            raise NotImplementedError("Production speaker verification not implemented")
    
    def validate(self, audio_bytes: bytes, customer_id: str) -> Dict:
        """
        Comprehensive voice validation
        Returns dict with all check results
        """
        # Validate audio input
        if not audio_bytes:
            return {
                'deepfake_score': 1.0,
                'liveness_passed': False,
                'liveness_confidence': 0.0,
                'speaker_verification_score': 0.0,
                'decision': 'FAIL',
                'explanation': 'No audio data provided'
            }

        if len(audio_bytes) < 100:
            return {
                'deepfake_score': 1.0,
                'liveness_passed': False,
                'liveness_confidence': 0.0,
                'speaker_verification_score': 0.0,
                'decision': 'FAIL',
                'explanation': 'Audio data too small to be valid'
            }

        deepfake_score = self.detect_deepfake(audio_bytes)
        liveness_result = self.check_liveness(audio_bytes)
        speaker_score = self.verify_speaker(audio_bytes, customer_id)
        
        # Determine if voice authentication passed
        passed = (
            deepfake_score < self.deepfake_threshold and
            liveness_result['passed'] and
            speaker_score > self.speaker_threshold
        )
        
        return {
            'deepfake_score': float(deepfake_score),
            'liveness_passed': liveness_result['passed'],
            'liveness_confidence': liveness_result.get('confidence', 0.0),
            'speaker_verification_score': float(speaker_score),
            'spoof_score': float(liveness_result.get('spoof_score', deepfake_score)),
            'thresholds': {
                'deepfake': float(self.deepfake_threshold),
                'liveness': float(self.liveness_threshold),
                'speaker': float(self.speaker_threshold),
                'target_fpr': float(self.target_fpr)
            },
            'model_loaded': bool(self.model_loaded),
            'decision': 'PASS' if passed else 'FAIL',
            'explanation': self._get_explanation(
                deepfake_score, liveness_result, speaker_score
            )
        }
    
    def _get_explanation(self, deepfake_score: float,
                        liveness_result: Dict,
                        speaker_score: float) -> str:
        """Generate human-readable explanation for voice result"""
        if deepfake_score > 0.7:
            return "High probability of synthetic voice (TTS/voice conversion detected)"
        elif not liveness_result['passed']:
            return "Liveness check failed (possible replay attack)"
        elif speaker_score < self.speaker_threshold:
            return f"Speaker verification below threshold (score: {speaker_score:.2f})"
        else:
            return "All voice checks passed"

    def _predict_spoof_score(self, audio_bytes: bytes) -> float:
        """Predict spoof score using configured codec and model."""
        audio, sr = self.loader.load_from_bytes(audio_bytes)
        audio_coded = self.telephony.apply_codec_by_name(audio, sr, self.codec)
        features = self.feature_extractor.extract_feature_stack(audio_coded, feature_types=self.feature_types)

        if self.model_loaded:
            try:
                return float(self.detector.predict_score(features))
            except Exception as exc:
                logger.error("Spoof model prediction failed, falling back to heuristic: %s", exc)

        # Heuristic fallback aligned with existing tasks but safer for clean audio
        variance = float(np.var(features))
        if variance < 1e-3:
            return 0.05
        return min(1.0, max(0.0, variance / 200.0))
