"""
Detection Tasks
Celery tasks for deepfake and spoof detection.
"""

import sys
from pathlib import Path
import logging
import time
import yaml

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery_app import app  # noqa: E402
from backend.utils.celery_utils import (  # noqa: E402
    create_task_result,
    update_task_progress,
)

logger = logging.getLogger(__name__)


def _load_voice_config() -> dict:
    """Load voice config from settings.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    if config_path.exists():
        try:
            with open(config_path) as f:
                settings = yaml.safe_load(f) or {}
                return settings.get("voice", {})
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Failed to load voice config: {exc}")
    return {}


def _resolve_model_path() -> Path:
    """Resolve model path from config or default gmm_test.pkl."""
    voice_cfg = _load_voice_config()
    model_path = voice_cfg.get("model_path")
    if model_path:
        candidate = Path(model_path)
        if not candidate.is_absolute():
            candidate = Path(__file__).parent.parent / candidate
    else:
        candidate = Path(__file__).parent.parent / "models" / "gmm_test.pkl"
    return candidate


def _resolve_threshold(key: str, default: float) -> float:
    voice_cfg = _load_voice_config()
    return float(voice_cfg.get(key, default))


@app.task(
    bind=True,
    name="tasks.detection_tasks.detect_deepfake",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def detect_deepfake(self, features: list, threshold: float = None):
    """
    Run deepfake detection on extracted features.

    Args:
        features: Feature matrix as list (from extract_features task)
        threshold: Detection threshold (lower = more sensitive)

    Returns:
        Dictionary with detection results
    """
    try:
        import numpy as np

        start_time = time.time()

        update_task_progress(self, 10, "Loading detection model")

        # Convert features
        features_array = np.array(features, dtype=np.float32)

        if threshold is None:
            threshold = _resolve_threshold("deepfake_threshold", 0.3)

        update_task_progress(self, 30, "Running deepfake detection")

        # Load model
        from models.baseline import GMMSpoofDetector

        model_path = _resolve_model_path()

        detector = GMMSpoofDetector()
        model_loaded = False

        if model_path.exists():
            try:
                detector.load(str(model_path))
                model_loaded = True
                logger.info(f"Loaded detection model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")

        update_task_progress(self, 70, "Computing scores")

        if model_loaded:
            deepfake_score = detector.predict_score(features_array)
        else:
            # Placeholder heuristic
            variance = np.var(features_array)
            deepfake_score = min(1.0, max(0.0, variance / 100.0))
            logger.warning("No trained model available, using placeholder score")

        is_deepfake = deepfake_score > threshold

        update_task_progress(self, 90, "Finalizing")

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "deepfake_score": float(deepfake_score),
                "threshold": float(threshold),
                "is_deepfake": bool(is_deepfake),
                "model_loaded": model_loaded,
                "confidence": float(1.0 - abs(deepfake_score - threshold)),
                "processing_time_seconds": elapsed,
            },
        )

        return result

    except Exception as e:
        logger.error(f"Deepfake detection failed: {e}")
        return create_task_result(status="FAILED", error=str(e))


@app.task(
    bind=True,
    name="tasks.detection_tasks.detect_spoof",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def detect_spoof(self, features: list, codec_name: str = "landline", threshold: float = None):
    """
    Run physics-based spoof detection on extracted features.

    Args:
        features: Feature matrix as list
        codec_name: Codec that was applied to the audio
        threshold: Detection threshold

    Returns:
        Dictionary with spoof detection results
    """
    try:
        import numpy as np

        start_time = time.time()

        update_task_progress(self, 10, "Preparing detection")

        # Convert features
        features_array = np.array(features, dtype=np.float32)

        if threshold is None:
            threshold = _resolve_threshold("liveness_threshold", 0.3)

        update_task_progress(self, 30, "Running spoof detection")

        # Load model
        from models.baseline import GMMSpoofDetector

        model_path = _resolve_model_path()

        detector = GMMSpoofDetector()
        model_loaded = False

        if model_path.exists():
            try:
                detector.load(str(model_path))
                model_loaded = True
            except Exception as e:
                logger.warning(f"Could not load model: {e}")

        update_task_progress(self, 60, "Computing spoof score")

        if model_loaded:
            spoof_score = detector.predict_score(features_array)
        else:
            # Placeholder heuristic
            variance = np.var(features_array)
            spoof_score = min(1.0, max(0.0, variance / 100.0))

        update_task_progress(self, 80, "Creating risk factors")

        # Create physics-based factor
        from risk_engine.factors import RiskEngine

        physics_factor = RiskEngine.create_physics_factor(
            spoof_score=spoof_score, codec_name=codec_name, threshold=threshold, weight=2.0
        )

        is_spoof = spoof_score > threshold

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "spoof_score": float(spoof_score),
                "threshold": float(threshold),
                "is_spoof": bool(is_spoof),
                "codec_applied": codec_name,
                "model_loaded": model_loaded,
                "physics_factor": {
                    "name": physics_factor.name,
                    "score": float(physics_factor.score),
                    "weight": float(physics_factor.weight),
                    "explanation": physics_factor.explanation,
                },
                "processing_time_seconds": elapsed,
            },
        )

        return result

    except Exception as e:
        logger.error(f"Spoof detection failed: {e}")
        return create_task_result(status="FAILED", error=str(e))
