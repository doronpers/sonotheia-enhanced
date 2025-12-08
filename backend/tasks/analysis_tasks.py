"""
Analysis Tasks
Celery tasks for full call analysis pipeline.
"""

import sys
from pathlib import Path
import logging
import time
import yaml

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery_app import app  # noqa: E402
from utils.celery_utils import (  # noqa: E402
    numpy_to_native,
    create_task_result,
    update_task_progress,
    validate_audio_data,
)

logger = logging.getLogger(__name__)


def _load_voice_config() -> dict:
    """Load voice config for detection thresholds and model path."""
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
    name="tasks.analysis_tasks.analyze_call_async",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def analyze_call_async(
    self,
    audio_data_base64: str,
    call_id: str,
    customer_id: str,
    transaction_id: str = None,
    amount_usd: float = None,
    destination_country: str = None,
    channel: str = "phone",
    codec: str = "landline",
):
    """
    Run full call analysis asynchronously.

    This task combines:
    - Audio loading and codec simulation
    - Feature extraction
    - Deepfake/spoof detection
    - Risk scoring
    - SAR generation (if high risk)

    Args:
        audio_data_base64: Base64 encoded audio data
        call_id: Unique call identifier
        customer_id: Customer identifier
        transaction_id: Optional transaction ID
        amount_usd: Optional transaction amount
        destination_country: Optional destination country
        channel: Call channel (phone, voip, etc.)
        codec: Codec to simulate

    Returns:
        Complete analysis result
    """
    try:
        import base64
        import numpy as np

        start_time = time.time()

        voice_cfg = _load_voice_config()
        sample_rate = int(voice_cfg.get("sample_rate", 16000))

        logger.info(f"Starting async analysis for call: {call_id}")

        # Step 1: Decode and load audio (10%)
        update_task_progress(self, 5, "Decoding audio data")
        audio_bytes = base64.b64decode(audio_data_base64)
        validate_audio_data(audio_bytes)

        update_task_progress(self, 10, "Loading audio")
        from data_ingest.loader import AudioLoader

        loader = AudioLoader(target_sr=sample_rate)
        audio, sr = loader.load_from_bytes(audio_bytes)
        duration = len(audio) / sr
        logger.info(f"Loaded audio: duration={duration:.2f}s, sr={sr}")

        # Step 2: Apply codec simulation (25%)
        update_task_progress(self, 20, f"Applying {codec} codec simulation")
        from telephony.pipeline import TelephonyPipeline

        telephony = TelephonyPipeline()

        if codec not in ["landline", "mobile", "voip", "clean"]:
            codec = "landline"

        audio_coded = telephony.apply_codec_by_name(audio, sr, codec)

        # Step 3: Extract features (50%)
        update_task_progress(self, 40, "Extracting audio features")
        from features.extraction import FeatureExtractor

        extractor = FeatureExtractor(sr=sample_rate)
        features = extractor.extract_feature_stack(audio_coded, feature_types=["lfcc", "logspec"])
        logger.info(f"Extracted features: shape={features.shape}")

        # Step 4: Run detection (70%)
        update_task_progress(self, 60, "Running deepfake detection")
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

        if model_loaded:
            spoof_score = detector.predict_score(features)
        else:
            variance = np.var(features)
            spoof_score = min(1.0, max(0.0, variance / 100.0))
            logger.warning("No trained model, using placeholder spoof score")

        # Step 5: Compute risk (85%)
        update_task_progress(self, 75, "Computing risk factors")
        from risk_engine.factors import RiskEngine

        factors = []

        threshold = _resolve_threshold("deepfake_threshold", 0.30)

        # Physics-based deepfake factor
        physics_factor = RiskEngine.create_physics_factor(
            spoof_score=spoof_score, codec_name=codec, threshold=threshold, weight=2.0
        )
        factors.append(physics_factor)

        # Placeholder ASV factor
        asv_factor = RiskEngine.create_asv_factor(score=0.15, weight=1.5)
        factors.append(asv_factor)

        # Placeholder liveness factor
        liveness_factor = RiskEngine.create_liveness_factor(score=0.10, weight=1.5)
        factors.append(liveness_factor)

        # Placeholder device factor
        device_factor = RiskEngine.create_device_factor(score=0.20, weight=1.0)
        factors.append(device_factor)

        risk_result = RiskEngine.compute_overall_risk(factors)

        # Step 6: Generate SAR if needed (95%)
        sar_narrative = None
        if risk_result.risk_level in ["HIGH", "CRITICAL"]:
            update_task_progress(self, 85, "Generating SAR narrative")
            sar_narrative = _generate_sar_narrative_helper(
                call_id=call_id,
                customer_id=customer_id,
                transaction_id=transaction_id,
                amount_usd=amount_usd,
                destination_country=destination_country,
                channel=channel,
                risk_result=risk_result,
            )

        # Step 7: Create visualization data
        update_task_progress(self, 95, "Preparing visualization data")
        viz_data = _create_visualization_data(audio, audio_coded, sr)

        elapsed = time.time() - start_time

        # Compile final result
        result = create_task_result(
            status="COMPLETED",
            data={
                "call_id": call_id,
                "customer_id": customer_id,
                "risk_result": {
                    "overall_score": float(risk_result.overall_score),
                    "risk_level": risk_result.risk_level,
                    "decision": risk_result.decision,
                    "factors": [
                        {
                            "name": f.name,
                            "score": float(f.score),
                            "weight": float(f.weight),
                            "explanation": f.explanation,
                        }
                        for f in risk_result.factors
                    ],
                },
                "detection": {
                    "spoof_score": float(spoof_score),
                    "model_loaded": model_loaded,
                },
                "audio_metadata": {
                    "duration_seconds": float(duration),
                    "sample_rate": sr,
                    "codec_applied": codec,
                    "num_frames": features.shape[0],
                    "feature_dims": features.shape[1],
                },
                "visualization_data": viz_data,
                "sar_narrative": sar_narrative,
                "processing_time_seconds": elapsed,
            },
        )

        logger.info(
            f"Analysis complete: call_id={call_id}, " f"risk={risk_result.overall_score:.3f}, time={elapsed:.2f}s"
        )

        return result

    except Exception as e:
        logger.error(f"Analysis failed for call {call_id}: {e}")
        return create_task_result(status="FAILED", error=str(e))


@app.task(
    bind=True,
    name="tasks.analysis_tasks.run_full_analysis",
    max_retries=2,
    soft_time_limit=300,
    time_limit=600,
)
def run_full_analysis(self, audio_data: list, sample_rate: int, metadata: dict):
    """
    Run full analysis on pre-processed audio data.

    This is a lighter version that takes already-loaded audio.

    Args:
        audio_data: Audio samples as list
        sample_rate: Audio sample rate
        metadata: Call metadata dictionary

    Returns:
        Analysis result
    """
    try:
        import numpy as np

        start_time = time.time()

        call_id = metadata.get("call_id", "unknown")
        codec = metadata.get("codec", "landline")

        logger.info(f"Running full analysis for call: {call_id}")

        # Convert audio
        audio = np.array(audio_data, dtype=np.float32)

        update_task_progress(self, 20, "Extracting features")

        # Extract features
        from features.extraction import FeatureExtractor

        extractor = FeatureExtractor(sr=sample_rate)
        features = extractor.extract_feature_stack(audio, feature_types=["lfcc", "logspec"])

        update_task_progress(self, 50, "Running detection")

        # Run detection
        from models.baseline import GMMSpoofDetector

        detector = GMMSpoofDetector()

        # Try to load model
        model_path = _resolve_model_path()
        model_loaded = False
        if model_path.exists():
            try:
                detector.load(str(model_path))
                model_loaded = True
            except Exception:
                pass

        if model_loaded:
            spoof_score = detector.predict_score(features)
        else:
            variance = np.var(features)
            spoof_score = min(1.0, max(0.0, variance / 100.0))

        update_task_progress(self, 80, "Computing risk")

        # Compute risk
        from risk_engine.factors import RiskEngine

        threshold = _resolve_threshold("deepfake_threshold", 0.30)

        factors = [
            RiskEngine.create_physics_factor(spoof_score=spoof_score, codec_name=codec, threshold=threshold, weight=2.0),
            RiskEngine.create_asv_factor(score=0.15, weight=1.5),
            RiskEngine.create_liveness_factor(score=0.10, weight=1.5),
            RiskEngine.create_device_factor(score=0.20, weight=1.0),
        ]

        risk_result = RiskEngine.compute_overall_risk(factors)

        elapsed = time.time() - start_time

        result = create_task_result(
            status="COMPLETED",
            data={
                "call_id": call_id,
                "spoof_score": float(spoof_score),
                "risk_level": risk_result.risk_level,
                "overall_risk": float(risk_result.overall_score),
                "decision": risk_result.decision,
                "model_loaded": model_loaded,
                "processing_time_seconds": elapsed,
            },
        )

        return result

    except Exception as e:
        logger.error(f"Full analysis failed: {e}")
        return create_task_result(status="FAILED", error=str(e))


def _generate_sar_narrative_helper(
    call_id: str,
    customer_id: str,
    transaction_id: str,
    amount_usd: float,
    destination_country: str,
    channel: str,
    risk_result,
) -> str:
    """Generate SAR narrative for high-risk calls."""
    amount_str = f"${amount_usd:,.2f}" if amount_usd else "N/A"

    narrative = f"""
SUSPICIOUS ACTIVITY REPORT - VOICE DEEPFAKE DETECTION

CALL INFORMATION:
- Call ID: {call_id}
- Customer ID: {customer_id}
- Transaction ID: {transaction_id or 'N/A'}
- Amount: {amount_str} USD
- Destination: {destination_country or 'N/A'}
- Channel: {channel}

RISK ASSESSMENT:
- Overall Risk Score: {risk_result.overall_score:.2%}
- Risk Level: {risk_result.risk_level}
- Recommended Decision: {risk_result.decision}

FACTOR ANALYSIS:
"""
    for factor in risk_result.factors:
        narrative += f"""
- {factor.name.upper()}:
  Score: {factor.score:.2%} (Weight: {factor.weight})
  {factor.explanation}
"""

    narrative += """
RECOMMENDATION:
Based on the risk factors above, this call requires further investigation.
Manual review is recommended before proceeding with the transaction.

Generated by Sonotheia MVP - Async Task Processing
"""
    return narrative


def _create_visualization_data(audio_orig, audio_coded, sr: int) -> dict:
    """Create data for waveform visualization."""
    import numpy as np

    # Downsample for visualization (max 1000 points)
    max_points = 1000
    if len(audio_orig) > max_points:
        step = len(audio_orig) // max_points
        waveform_orig = audio_orig[::step][:max_points]
        waveform_coded = audio_coded[::step][:max_points]
    else:
        waveform_orig = audio_orig
        waveform_coded = audio_coded

    # Time axis
    time = np.linspace(0, len(audio_orig) / sr, len(waveform_orig))

    viz_data = {
        "waveform": {
            "time": numpy_to_native(time),
            "amplitude_original": numpy_to_native(waveform_orig),
            "amplitude_coded": numpy_to_native(waveform_coded),
        }
    }

    return viz_data
