"""
Transcription Module Tests

Unit and integration tests for the transcription module.
"""

import pytest
import base64
import numpy as np
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from api.main import app

# Create test client
client = TestClient(app)


def generate_test_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate a simple test WAV file as bytes."""
    import struct
    
    # Generate sine wave samples
    num_samples = int(duration_seconds * sample_rate)
    frequency = 440  # Hz
    t = np.linspace(0, duration_seconds, num_samples, dtype=np.float32)
    samples = (np.sin(2 * np.pi * frequency * t) * 0.3).astype(np.float32)
    
    # Convert to 16-bit PCM
    samples_int = (samples * 32767).astype(np.int16)
    
    # Build WAV header
    channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = num_samples * channels * bits_per_sample // 8
    
    # RIFF header
    wav_bytes = b'RIFF'
    wav_bytes += struct.pack('<I', 36 + data_size)  # File size - 8
    wav_bytes += b'WAVE'
    
    # fmt chunk
    wav_bytes += b'fmt '
    wav_bytes += struct.pack('<I', 16)  # Chunk size
    wav_bytes += struct.pack('<H', 1)   # Audio format (PCM)
    wav_bytes += struct.pack('<H', channels)
    wav_bytes += struct.pack('<I', sample_rate)
    wav_bytes += struct.pack('<I', byte_rate)
    wav_bytes += struct.pack('<H', block_align)
    wav_bytes += struct.pack('<H', bits_per_sample)
    
    # data chunk
    wav_bytes += b'data'
    wav_bytes += struct.pack('<I', data_size)
    wav_bytes += samples_int.tobytes()
    
    return wav_bytes


class TestTranscriptionModels:
    """Test transcription Pydantic models."""
    
    def test_transcript_segment_model(self):
        """Test TranscriptSegment model validation."""
        from transcription.models import TranscriptSegment
        
        # Valid segment
        segment = TranscriptSegment(
            start_time=0.0,
            end_time=2.5,
            text="Hello, world!",
            confidence=0.95,
            speaker="SPEAKER_00"
        )
        assert segment.start_time == 0.0
        assert segment.end_time == 2.5
        assert segment.text == "Hello, world!"
        assert segment.confidence == 0.95
        assert segment.speaker == "SPEAKER_00"
    
    def test_transcript_segment_validation(self):
        """Test TranscriptSegment validation rules."""
        from transcription.models import TranscriptSegment
        
        # Empty text should fail
        with pytest.raises(ValueError):
            TranscriptSegment(
                start_time=0.0,
                end_time=1.0,
                text="   ",  # Empty after strip
                confidence=0.9
            )
        
        # Negative start_time should fail
        with pytest.raises(ValueError):
            TranscriptSegment(
                start_time=-1.0,
                end_time=1.0,
                text="Hello",
                confidence=0.9
            )
    
    def test_transcript_model(self):
        """Test Transcript model."""
        from transcription.models import Transcript, TranscriptSegment
        
        segment = TranscriptSegment(
            start_time=0.0,
            end_time=2.5,
            text="Hello, world!",
            confidence=0.95
        )
        
        transcript = Transcript(
            audio_id="test-audio-123",
            language="en",
            duration=10.5,
            segments=[segment],
            full_text="Hello, world!"
        )
        
        assert transcript.audio_id == "test-audio-123"
        assert transcript.language == "en"
        assert transcript.duration == 10.5
        assert len(transcript.segments) == 1
    
    def test_transcription_request_validation(self):
        """Test TranscriptionRequest validation."""
        from transcription.models import TranscriptionRequest
        
        # Valid request
        request = TranscriptionRequest(
            audio_id="test-audio",
            audio_data_base64="dGVzdA==",  # "test" in base64
            provider="demo"
        )
        assert request.audio_id == "test-audio"
        assert request.provider == "demo"
        
        # Invalid provider
        with pytest.raises(ValueError):
            TranscriptionRequest(
                audio_id="test-audio",
                audio_data_base64="dGVzdA==",
                provider="invalid_provider"
            )
    
    def test_audio_id_validation(self):
        """Test audio_id format validation."""
        from transcription.models import TranscriptionRequest
        
        # Valid IDs
        for valid_id in ["test123", "test-audio", "test_audio", "test.audio"]:
            request = TranscriptionRequest(
                audio_id=valid_id,
                audio_data_base64="dGVzdA=="
            )
            assert request.audio_id == valid_id
        
        # Invalid IDs (special characters)
        for invalid_id in ["test<script>", "test;drop", "test audio"]:
            with pytest.raises(ValueError):
                TranscriptionRequest(
                    audio_id=invalid_id,
                    audio_data_base64="dGVzdA=="
                )


class TestTranscriptionConfig:
    """Test transcription configuration."""
    
    def test_config_defaults(self):
        """Test configuration default values."""
        from transcription.config import TranscriptionConfig, reset_config
        
        reset_config()
        config = TranscriptionConfig()
        
        assert config.max_audio_size_mb == 800
        assert config.sample_rate == 16000
        assert config.default_language == "en"
    
    def test_available_providers(self):
        """Test available providers list."""
        from transcription.config import TranscriptionConfig
        
        config = TranscriptionConfig()
        providers = config.get_available_providers()
        
        # Demo should always be available
        assert "demo" in providers
        
        # whisper_local should be available (even without model loaded)
        assert "whisper_local" in providers
    
    def test_config_to_dict(self):
        """Test config serialization."""
        from transcription.config import TranscriptionConfig
        
        config = TranscriptionConfig()
        config_dict = config.to_dict()
        
        assert "enabled" in config_dict
        assert "demo_mode" in config_dict
        assert "available_providers" in config_dict
        # API keys should not be exposed
        assert "has_openai_key" in config_dict
        assert "openai_api_key" not in config_dict


class TestDemoProvider:
    """Test demo transcription provider."""
    
    @pytest.mark.asyncio
    async def test_demo_transcribe(self):
        """Test demo provider transcription."""
        from transcription.providers.demo import DemoProvider
        from transcription.config import TranscriptionConfig
        
        config = TranscriptionConfig()
        provider = DemoProvider(config)
        
        # Generate test audio
        sample_rate = 16000
        duration = 10.0
        audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        transcript = await provider.transcribe(
            audio_data=audio_data,
            sample_rate=sample_rate,
            language="en",
            audio_id="test-demo"
        )
        
        assert transcript.audio_id == "test-demo"
        assert transcript.language == "en"
        assert transcript.duration == duration
        assert len(transcript.segments) > 0
        assert transcript.full_text != ""
    
    @pytest.mark.asyncio
    async def test_demo_provider_availability(self):
        """Test demo provider is always available."""
        from transcription.providers.demo import DemoProvider
        from transcription.config import TranscriptionConfig
        
        config = TranscriptionConfig()
        provider = DemoProvider(config)
        
        assert await provider.is_available() is True


class TestDiarization:
    """Test speaker diarization."""
    
    @pytest.mark.asyncio
    async def test_demo_diarization(self):
        """Test demo diarization."""
        from transcription.diarization import SpeakerDiarizer
        from transcription.config import TranscriptionConfig
        
        config = TranscriptionConfig()
        diarizer = SpeakerDiarizer(config)
        
        # Generate test audio
        sample_rate = 16000
        duration = 30.0
        audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        result = await diarizer.diarize(
            audio_data=audio_data,
            sample_rate=sample_rate,
            audio_id="test-diarize",
            num_speakers=2
        )
        
        assert result.audio_id == "test-diarize"
        assert result.num_speakers == 2
        assert result.duration == duration
        assert len(result.segments) > 0
    
    def test_merge_transcript_with_diarization(self):
        """Test merging transcript segments with diarization."""
        from transcription.diarization import SpeakerDiarizer
        from transcription.models import DiarizationSegment
        from transcription.config import TranscriptionConfig
        
        config = TranscriptionConfig()
        diarizer = SpeakerDiarizer(config)
        
        transcript_segments = [
            {"start": 0.0, "end": 5.0, "text": "Hello", "confidence": 0.9},
            {"start": 5.0, "end": 10.0, "text": "World", "confidence": 0.9},
        ]
        
        diarization_segments = [
            DiarizationSegment(start_time=0.0, end_time=6.0, speaker="SPEAKER_00", confidence=0.9),
            DiarizationSegment(start_time=6.0, end_time=12.0, speaker="SPEAKER_01", confidence=0.9),
        ]
        
        merged = diarizer.merge_transcript_with_diarization(
            transcript_segments, diarization_segments
        )
        
        assert len(merged) == 2
        assert merged[0]["speaker"] == "SPEAKER_00"
        assert merged[1]["speaker"] == "SPEAKER_01"


class TestTranscriptionAPI:
    """Test transcription API endpoints."""
    
    def test_transcription_health_endpoint(self):
        """Test transcription health check endpoint."""
        response = client.get("/api/transcribe/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "enabled" in data
        assert "demo_mode" in data
        assert "available_providers" in data
        assert "providers" in data
        assert "demo" in data["available_providers"]
    
    def test_transcription_config_endpoint(self):
        """Test transcription config endpoint."""
        response = client.get("/api/transcribe/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "max_audio_size_mb" in data
        assert "default_provider" in data
    
    def test_transcribe_with_demo_provider(self):
        """Test transcription with demo provider."""
        # Generate test WAV audio
        wav_bytes = generate_test_wav_bytes(duration_seconds=2.0)
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
        
        request_data = {
            "audio_id": "test-api-demo",
            "audio_data_base64": audio_base64,
            "provider": "demo",
            "language": "en",
            "enable_diarization": False
        }
        
        response = client.post("/api/transcribe", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["provider"] == "demo"
        assert "transcript" in data
        assert data["transcript"]["audio_id"] == "test-api-demo"
        assert len(data["transcript"]["segments"]) > 0
    
    def test_transcribe_with_diarization(self):
        """Test transcription with speaker diarization enabled."""
        wav_bytes = generate_test_wav_bytes(duration_seconds=5.0)
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
        
        request_data = {
            "audio_id": "test-api-diarize",
            "audio_data_base64": audio_base64,
            "provider": "demo",
            "enable_diarization": True,
            "num_speakers": 2
        }
        
        response = client.post("/api/transcribe", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "diarization" in data
        if data["diarization"]:
            assert data["diarization"]["num_speakers"] == 2
    
    def test_transcribe_invalid_audio(self):
        """Test transcription with invalid audio data."""
        request_data = {
            "audio_id": "test-invalid",
            "audio_data_base64": "not-valid-base64!!!",
            "provider": "demo"
        }
        
        response = client.post("/api/transcribe", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_transcribe_invalid_provider(self):
        """Test transcription with invalid provider."""
        wav_bytes = generate_test_wav_bytes(duration_seconds=1.0)
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
        
        request_data = {
            "audio_id": "test-invalid-provider",
            "audio_data_base64": audio_base64,
            "provider": "nonexistent_provider"
        }
        
        response = client.post("/api/transcribe", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_diarize_endpoint(self):
        """Test standalone diarization endpoint."""
        wav_bytes = generate_test_wav_bytes(duration_seconds=3.0)
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
        
        request_data = {
            "audio_id": "test-diarize-api",
            "audio_data_base64": audio_base64,
            "num_speakers": 2
        }
        
        response = client.post("/api/diarize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["audio_id"] == "test-diarize-api"
        assert data["num_speakers"] == 2
        assert len(data["segments"]) > 0


class TestAsyncTranscription:
    """Test async transcription jobs."""
    
    def test_async_job_submission(self):
        """Test async transcription job submission."""
        wav_bytes = generate_test_wav_bytes(duration_seconds=2.0)
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
        
        request_data = {
            "audio_id": "test-async",
            "audio_data_base64": audio_base64,
            "provider": "demo",
            "priority": "normal"
        }
        
        response = client.post("/api/transcribe/async", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert data["audio_id"] == "test-async"
        assert data["status"] == "pending"
        assert "endpoints" in data
    
    def test_job_status_not_found(self):
        """Test job status for non-existent job."""
        response = client.get("/api/transcribe/nonexistent-job-id")
        assert response.status_code == 404


class TestJSONSafety:
    """Test JSON serialization safety."""
    
    def test_numpy_type_conversion(self):
        """Test numpy types are converted to native Python types."""
        from transcription.providers.base import TranscriptionProvider
        from transcription.config import TranscriptionConfig
        
        class TestProvider(TranscriptionProvider):
            async def transcribe(self, *args, **kwargs):
                pass
            async def is_available(self):
                return True
        
        config = TranscriptionConfig()
        provider = TestProvider(config)
        
        # Test numpy type conversions
        assert provider._convert_numpy_to_native(np.int64(42)) == 42
        assert isinstance(provider._convert_numpy_to_native(np.int64(42)), int)
        
        assert provider._convert_numpy_to_native(np.float64(3.14)) == 3.14
        assert isinstance(provider._convert_numpy_to_native(np.float64(3.14)), float)
        
        arr = np.array([1, 2, 3])
        converted = provider._convert_numpy_to_native(arr)
        assert converted == [1, 2, 3]
        assert isinstance(converted, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
