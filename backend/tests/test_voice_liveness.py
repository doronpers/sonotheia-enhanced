import io
import numpy as np
import soundfile as sf
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from authentication.voice_factor import VoiceAuthenticator


def _make_wav_bytes(duration_sec: float = 0.2, sr: int = 16000) -> bytes:
    """Create a small sine wave WAV payload for testing."""
    t = np.linspace(0, duration_sec, int(sr * duration_sec), False)
    tone = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, tone, sr, format="WAV")
    return buffer.getvalue()


def test_voice_authenticator_uses_configured_thresholds_and_scores():
    audio_bytes = _make_wav_bytes()
    va = VoiceAuthenticator(
        {
            "deepfake_threshold": 0.3,
            "liveness_threshold": 0.25,
            "speaker_threshold": 0.5,
            "demo_mode": False,
            "model_path": "backend/models/nonexistent.pkl",
            "codec": "landline",
            "feature_types": ["lfcc"],
            "sample_rate": 16000,
            "target_fpr": 0.01,
        }
    )

    # Patch speaker verification to avoid NotImplemented in non-demo mode
    va.verify_speaker = lambda audio, cid: 0.9

    result = va.validate(audio_bytes, "cust123")

    assert result["decision"] == "PASS"
    assert result["model_loaded"] is False
    assert result["liveness_passed"] is True
    assert result["thresholds"]["liveness"] == 0.25
    assert "spoof_score" in result
    assert result["spoof_score"] < result["thresholds"]["liveness"]

