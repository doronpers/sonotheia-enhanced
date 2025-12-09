"""
Audio Processing Tasks
Celery tasks for audio loading, preprocessing, and feature extraction.
"""

import sys
from pathlib import Path
import logging
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery_app import app  # noqa: E402
from backend.utils.celery_utils import (  # noqa: E402
    numpy_to_native,
    create_task_result,
    update_task_progress,
    validate_audio_data,
)

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name="tasks.audio_tasks.process_audio",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def process_audio(self, audio_data_base64: str, codec: str = "landline", target_sr: int = 16000):
    """
    Process audio data: decode, resample, and apply codec simulation.

    Args:
        audio_data_base64: Base64 encoded audio data
        codec: Codec to simulate (landline, mobile, voip, clean)
        target_sr: Target sample rate

    Returns:
        Dictionary with processed audio data and metadata
    """
    try:
        import base64

        start_time = time.time()

        # Update progress
        update_task_progress(self, 10, "Decoding audio data")

        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data_base64)
        validate_audio_data(audio_bytes)

        update_task_progress(self, 30, "Loading audio")

        # Load audio using the existing loader
        from data_ingest.loader import AudioLoader

        loader = AudioLoader(target_sr=target_sr)
        audio, sr = loader.load_from_bytes(audio_bytes)

        duration = len(audio) / sr
        logger.info(f"Loaded audio: duration={duration:.2f}s, sr={sr}")

        update_task_progress(self, 50, f"Applying {codec} codec simulation")

        # Apply codec simulation
        from telephony.pipeline import TelephonyPipeline

        telephony = TelephonyPipeline()

        if codec not in ["landline", "mobile", "voip", "clean"]:
            logger.warning(f"Unknown codec {codec}, using landline")
            codec = "landline"

        audio_coded = telephony.apply_codec_by_name(audio, sr, codec)

        update_task_progress(self, 90, "Finalizing")

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "audio": numpy_to_native(audio_coded),
                "sample_rate": sr,
                "duration_seconds": float(duration),
                "codec_applied": codec,
                "original_size_bytes": len(audio_bytes),
                "processing_time_seconds": elapsed,
            },
        )

        return result

    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        return create_task_result(status="FAILED", error=str(e))


@app.task(
    bind=True,
    name="tasks.audio_tasks.extract_features",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=180,
    time_limit=240,
)
def extract_features(self, audio_data: list, sample_rate: int = 16000, feature_types: list = None):
    """
    Extract audio features for analysis.

    Args:
        audio_data: Audio samples as a list (from process_audio task)
        sample_rate: Sample rate of the audio
        feature_types: List of feature types to extract

    Returns:
        Dictionary with extracted features
    """
    try:
        import numpy as np

        start_time = time.time()

        if feature_types is None:
            feature_types = ["lfcc", "logspec"]

        update_task_progress(self, 10, "Converting audio data")

        # Convert list back to numpy array
        audio = np.array(audio_data, dtype=np.float32)

        update_task_progress(self, 30, "Extracting features")

        # Extract features
        from features.extraction import FeatureExtractor

        extractor = FeatureExtractor(sr=sample_rate)
        features = extractor.extract_feature_stack(audio, feature_types=feature_types)

        update_task_progress(self, 90, "Finalizing")

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "features": numpy_to_native(features),
                "feature_types": feature_types,
                "num_frames": features.shape[0],
                "feature_dims": features.shape[1],
                "processing_time_seconds": elapsed,
            },
        )

        return result

    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        return create_task_result(status="FAILED", error=str(e))
