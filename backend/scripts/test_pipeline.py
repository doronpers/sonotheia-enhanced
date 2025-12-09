"""
Quick Test of Sonotheia MVP Pipeline

Tests all components end-to-end with synthetic audio.
"""

import numpy as np
import logging
from pathlib import Path
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from telephony.pipeline import TelephonyPipeline
from features.extraction import FeatureExtractor
from models.baseline import GMMSpoofDetector
from risk_engine.factors import RiskEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_test_audio(duration: float = 2.0, sr: int = 16000) -> np.ndarray:
    """Generate synthetic test audio"""
    t = np.linspace(0, duration, int(sr * duration))

    # Sine wave with some harmonics
    audio = (
        0.5 * np.sin(2 * np.pi * 440 * t) +  # A4 note
        0.3 * np.sin(2 * np.pi * 880 * t) +  # Harmonic
        0.1 * np.sin(2 * np.pi * 1320 * t)   # Harmonic
    )

    # Add some noise
    audio += 0.05 * np.random.randn(len(audio))

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8

    return audio.astype(np.float32)


def test_telephony_pipeline():
    """Test telephony codec simulation"""
    logger.info("Testing telephony pipeline...")

    audio = generate_test_audio()
    sr = 16000

    telephony = TelephonyPipeline()

    # Test all codecs
    codecs = ['landline', 'mobile', 'voip', 'clean']
    for codec in codecs:
        audio_coded = telephony.apply_codec_by_name(audio, sr, codec)
        assert len(audio_coded) == len(audio), f"{codec} codec changed audio length"
        logger.info(f"✓ {codec} codec OK")

    logger.info("Telephony pipeline test PASSED")


def test_feature_extraction():
    """Test feature extraction"""
    logger.info("Testing feature extraction...")

    audio = generate_test_audio()
    sr = 16000

    extractor = FeatureExtractor(sr=sr)

    # Test LFCC
    lfcc = extractor.extract_lfcc(audio)
    assert lfcc.shape[1] == 20, "LFCC dimension mismatch"
    logger.info(f"✓ LFCC: shape={lfcc.shape}")

    # Test CQCC
    cqcc = extractor.extract_cqcc(audio)
    assert cqcc.shape[1] == 20, "CQCC dimension mismatch"
    logger.info(f"✓ CQCC: shape={cqcc.shape}")

    # Test log-spectrogram
    logspec = extractor.extract_logspec(audio)
    logger.info(f"✓ Log-spectrogram: shape={logspec.shape}")

    # Test feature stack
    features = extractor.extract_feature_stack(audio, feature_types=['lfcc', 'logspec'])
    logger.info(f"✓ Feature stack: shape={features.shape}")

    logger.info("Feature extraction test PASSED")


def test_spoof_detector():
    """Test spoof detector (without training)"""
    logger.info("Testing spoof detector...")

    audio = generate_test_audio()
    sr = 16000

    # Extract features
    extractor = FeatureExtractor(sr=sr)
    features = extractor.extract_feature_stack(audio, feature_types=['lfcc'])

    # Create detector (not trained, just testing structure)
    detector = GMMSpoofDetector(n_components=4)

    # Create some dummy training data
    genuine_features = features[:50]  # First 50 frames
    spoof_features = features[50:100]  # Next 50 frames

    # Train
    detector.train(genuine_features, spoof_features)
    logger.info("✓ Detector trained")

    # Predict
    score = detector.predict_score(features)
    assert 0 <= score <= 1, f"Score {score} out of range [0, 1]"
    logger.info(f"✓ Predicted score: {score:.3f}")

    # Test save/load
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        model_path = f.name

    detector.save(model_path)
    logger.info(f"✓ Saved model to {model_path}")

    detector2 = GMMSpoofDetector()
    detector2.load(model_path)
    score2 = detector2.predict_score(features)
    assert abs(score - score2) < 1e-6, "Loaded model gives different scores"
    logger.info("✓ Loaded model and verified consistency")

    # Cleanup
    Path(model_path).unlink()

    logger.info("Spoof detector test PASSED")


def test_risk_engine():
    """Test risk engine"""
    logger.info("Testing risk engine...")

    # Create factors
    physics_factor = RiskEngine.create_physics_factor(
        spoof_score=0.25,
        codec_name='landline',
        threshold=0.30,
        weight=2.0
    )
    logger.info(f"✓ Physics factor: score={physics_factor.score:.2f}")

    asv_factor = RiskEngine.create_asv_factor(score=0.15, weight=1.5)
    logger.info(f"✓ ASV factor: score={asv_factor.score:.2f}")

    liveness_factor = RiskEngine.create_liveness_factor(score=0.10, weight=1.5)
    logger.info(f"✓ Liveness factor: score={liveness_factor.score:.2f}")

    # Compute overall risk
    factors = [physics_factor, asv_factor, liveness_factor]
    risk_result = RiskEngine.compute_overall_risk(factors)

    assert 0 <= risk_result.overall_score <= 1, "Overall score out of range"
    assert risk_result.risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], "Invalid risk level"
    assert risk_result.decision in ['APPROVE', 'DECLINE', 'REVIEW'], "Invalid decision"

    logger.info(f"✓ Overall risk: {risk_result.overall_score:.3f}")
    logger.info(f"✓ Risk level: {risk_result.risk_level}")
    logger.info(f"✓ Decision: {risk_result.decision}")

    logger.info("Risk engine test PASSED")


def test_end_to_end_pipeline():
    """Test complete end-to-end pipeline"""
    logger.info("Testing end-to-end pipeline...")

    # Generate test audio
    audio = generate_test_audio(duration=3.0)
    sr = 16000

    # 1. Apply codec
    telephony = TelephonyPipeline()
    audio_coded = telephony.apply_landline_chain(audio, sr)
    logger.info("✓ Step 1: Applied codec")

    # 2. Extract features
    extractor = FeatureExtractor(sr=sr)
    features = extractor.extract_feature_stack(audio_coded, feature_types=['lfcc', 'logspec'])
    logger.info(f"✓ Step 2: Extracted features: shape={features.shape}")

    # 3. Train quick model (simplified)
    detector = GMMSpoofDetector(n_components=4)
    genuine_features = features[:100]
    spoof_features = features[100:200]
    detector.train(genuine_features, spoof_features)
    logger.info("✓ Step 3: Trained detector")

    # 4. Predict spoof score
    spoof_score = detector.predict_score(features)
    logger.info(f"✓ Step 4: Predicted spoof score: {spoof_score:.3f}")

    # 5. Create risk factors
    physics_factor = RiskEngine.create_physics_factor(spoof_score, codec_name='landline')
    asv_factor = RiskEngine.create_asv_factor()
    liveness_factor = RiskEngine.create_liveness_factor()
    factors = [physics_factor, asv_factor, liveness_factor]
    logger.info("✓ Step 5: Created risk factors")

    # 6. Compute overall risk
    risk_result = RiskEngine.compute_overall_risk(factors)
    logger.info(f"✓ Step 6: Computed risk: {risk_result.overall_score:.3f} ({risk_result.risk_level})")

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("END-TO-END PIPELINE SUMMARY")
    logger.info("="*60)
    logger.info("Audio duration: 3.0s")
    logger.info("Codec: landline")
    logger.info(f"Features: {features.shape[0]} frames x {features.shape[1]} dims")
    logger.info(f"Spoof score: {spoof_score:.3f}")
    logger.info(f"Overall risk: {risk_result.overall_score:.3f}")
    logger.info(f"Risk level: {risk_result.risk_level}")
    logger.info(f"Decision: {risk_result.decision}")
    logger.info("="*60 + "\n")

    logger.info("End-to-end pipeline test PASSED")


def main():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("SONOTHEIA MVP PIPELINE TEST")
    logger.info("="*60 + "\n")

    try:
        test_telephony_pipeline()
        logger.info("")

        test_feature_extraction()
        logger.info("")

        test_spoof_detector()
        logger.info("")

        test_risk_engine()
        logger.info("")

        test_end_to_end_pipeline()

        logger.info("\n" + "="*60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("="*60 + "\n")

        logger.info("The Sonotheia MVP pipeline is working correctly!")
        logger.info("Next steps:")
        logger.info("1. Start the API: uvicorn api.main:app --reload")
        logger.info("2. Start the UI: streamlit run ui/streamlit_app.py")
        logger.info("3. Upload audio and test the full system")

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
