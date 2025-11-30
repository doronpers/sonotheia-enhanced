"""
Detection Pipeline Tests

Tests for the 6-stage audio deepfake detection pipeline.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from detection import DetectionPipeline, get_pipeline, convert_numpy_types
from detection.config import DetectionConfig


class TestNumpyUtils:
    """Test numpy serialization utilities."""

    def test_convert_numpy_scalar(self):
        """Test converting numpy scalars to Python types."""
        result = convert_numpy_types(np.float64(0.95))
        assert isinstance(result, float)
        assert result == 0.95

    def test_convert_numpy_int(self):
        """Test converting numpy integers."""
        result = convert_numpy_types(np.int64(42))
        assert isinstance(result, int)
        assert result == 42

    def test_convert_numpy_array(self):
        """Test converting numpy arrays to lists."""
        arr = np.array([1, 2, 3])
        result = convert_numpy_types(arr)
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_convert_nested_dict(self):
        """Test converting nested dictionary with numpy types."""
        data = {
            "score": np.float64(0.85),
            "values": np.array([1.0, 2.0, 3.0]),
            "nested": {
                "count": np.int32(10),
            }
        }
        result = convert_numpy_types(data)

        assert isinstance(result["score"], float)
        assert isinstance(result["values"], list)
        assert isinstance(result["nested"]["count"], int)

    def test_convert_preserves_native_types(self):
        """Test that native Python types are preserved."""
        data = {
            "name": "test",
            "count": 5,
            "enabled": True,
            "rate": 0.5,
        }
        result = convert_numpy_types(data)
        assert result == data


class TestDetectionConfig:
    """Test detection configuration."""

    def test_default_config(self):
        """Test default configuration creation."""
        config = DetectionConfig()
        assert config.demo_mode is True
        assert config.min_audio_duration == 0.5
        assert config.max_audio_duration == 300.0

    def test_config_from_dict(self):
        """Test configuration from dictionary."""
        data = {
            "demo_mode": False,
            "feature_extraction": {
                "sample_rate": 22050,
            }
        }
        config = DetectionConfig.from_dict(data)
        assert config.demo_mode is False
        assert config.feature_extraction.sample_rate == 22050


class TestDetectionPipeline:
    """Test detection pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline fixture."""
        return DetectionPipeline()

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio."""
        sr = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
        return audio.astype(np.float32)

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes correctly."""
        assert pipeline is not None
        assert pipeline.config is not None
        assert pipeline.feature_extraction is not None
        assert pipeline.temporal_analysis is not None
        assert pipeline.artifact_detection is not None
        assert pipeline.rawnet3 is not None
        assert pipeline.fusion_engine is not None
        assert pipeline.explainability is not None

    def test_full_pipeline_detection(self, pipeline, sample_audio):
        """Test full detection pipeline."""
        result = pipeline.detect(sample_audio, quick_mode=False)

        assert result["success"] is True
        assert "detection_score" in result
        assert 0.0 <= result["detection_score"] <= 1.0
        assert "is_spoof" in result
        assert "confidence" in result
        assert "decision" in result
        assert "job_id" in result
        assert "stage_results" in result

    def test_quick_pipeline_detection(self, pipeline, sample_audio):
        """Test quick detection pipeline (stages 1-3)."""
        result = pipeline.detect(sample_audio, quick_mode=True)

        assert result["success"] is True
        assert result["quick_mode"] is True
        assert "detection_score" in result
        assert "stage_results" in result
        # Quick mode should only have stages 1-3
        stage_results = result["stage_results"]
        assert "feature_extraction" in stage_results
        assert "temporal_analysis" in stage_results
        assert "artifact_detection" in stage_results
        assert "rawnet3" not in stage_results

    def test_demo_mode_enabled(self, pipeline, sample_audio):
        """Test demo mode is enabled in pipeline."""
        result = pipeline.detect(sample_audio)

        assert result["demo_mode"] is True

    def test_audio_too_short_rejected(self, pipeline):
        """Test that audio shorter than minimum is rejected."""
        short_audio = np.zeros(100, dtype=np.float32)  # Very short
        result = pipeline.detect(short_audio)

        # Should fail due to duration
        assert result["success"] is False or "error" in result

    def test_result_json_serializable(self, pipeline, sample_audio):
        """Test that result is JSON serializable."""
        import json

        result = pipeline.detect(sample_audio)

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Verify round-trip
        loaded = json.loads(json_str)
        assert loaded["success"] == result["success"]

    def test_job_status_tracking(self, pipeline, sample_audio):
        """Test job status is tracked."""
        result = pipeline.detect(sample_audio)
        job_id = result.get("job_id")

        assert job_id is not None

        status = pipeline.get_job_status(job_id)
        assert status["job_id"] == job_id
        assert status["status"] == "completed"


class TestFeatureExtractionStage:
    """Test feature extraction stage."""

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio."""
        sr = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        return audio.astype(np.float32)

    def test_feature_extraction(self, sample_audio):
        """Test feature extraction stage."""
        from detection.stages import FeatureExtractionStage

        stage = FeatureExtractionStage()
        result = stage.process(sample_audio)

        assert result["success"] is True
        assert "features" in result
        assert "combined_features" in result
        assert "anomaly_score" in result
        assert 0.0 <= result["anomaly_score"] <= 1.0

    def test_empty_audio_handled(self):
        """Test empty audio is handled gracefully."""
        from detection.stages import FeatureExtractionStage

        stage = FeatureExtractionStage()
        result = stage.process(np.array([]))

        assert result["success"] is False
        assert "error" in result


class TestTemporalAnalysisStage:
    """Test temporal analysis stage."""

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio."""
        sr = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
        return audio.astype(np.float32)

    def test_temporal_analysis(self, sample_audio):
        """Test temporal analysis stage."""
        from detection.stages import TemporalAnalysisStage

        stage = TemporalAnalysisStage()
        result = stage.process(sample_audio)

        assert result["success"] is True
        assert "temporal_score" in result
        assert "discontinuities" in result
        assert "energy_envelope" in result


class TestArtifactDetectionStage:
    """Test artifact detection stage."""

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio."""
        sr = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
        return audio.astype(np.float32)

    def test_artifact_detection(self, sample_audio):
        """Test artifact detection stage."""
        from detection.stages import ArtifactDetectionStage

        stage = ArtifactDetectionStage()
        result = stage.process(sample_audio)

        assert result["success"] is True
        assert "artifact_score" in result
        assert "silence_artifacts" in result
        assert "click_artifacts" in result
        assert "total_artifacts" in result


class TestRawNet3Stage:
    """Test RawNet3 stage."""

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio."""
        sr = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
        return audio.astype(np.float32)

    def test_rawnet3_demo_mode(self, sample_audio):
        """Test RawNet3 in demo mode."""
        from detection.stages import RawNet3Stage

        stage = RawNet3Stage(demo_mode=True)
        result = stage.process(sample_audio)

        assert result["success"] is True
        assert "score" in result
        assert 0.0 <= result["score"] <= 1.0
        assert result["demo_mode"] is True


class TestFusionEngine:
    """Test fusion engine."""

    def test_weighted_average_fusion(self):
        """Test weighted average fusion."""
        from detection.stages import FusionEngine

        stage_results = {
            "feature_extraction": {"success": True, "anomaly_score": 0.3},
            "temporal_analysis": {"success": True, "temporal_score": 0.4},
            "artifact_detection": {"success": True, "artifact_score": 0.2},
            "rawnet3": {"success": True, "score": 0.5},
        }

        engine = FusionEngine(fusion_method="weighted_average")
        result = engine.fuse(stage_results)

        assert result["success"] is True
        assert "fused_score" in result
        assert 0.0 <= result["fused_score"] <= 1.0
        assert "decision" in result

    def test_max_fusion(self):
        """Test max fusion."""
        from detection.stages import FusionEngine

        stage_results = {
            "feature_extraction": {"success": True, "anomaly_score": 0.3},
            "rawnet3": {"success": True, "score": 0.8},
        }

        engine = FusionEngine(fusion_method="max")
        result = engine.fuse(stage_results)

        assert result["fused_score"] == 0.8


class TestExplainabilityStage:
    """Test explainability stage."""

    def test_explainability_generation(self):
        """Test explanation generation."""
        from detection.stages import ExplainabilityStage

        stage_results = {
            "feature_extraction": {
                "success": True,
                "anomaly_score": 0.3,
                "num_frames": 100,
            },
            "temporal_analysis": {
                "success": True,
                "temporal_score": 0.4,
                "num_anomalies": 2,
            },
            "rawnet3": {
                "success": True,
                "score": 0.2,
                "demo_mode": True,
            },
        }

        fusion_result = {
            "success": True,
            "fused_score": 0.3,
            "confidence": 0.85,
            "decision": "GENUINE_LIKELY",
            "fusion_method": "weighted_average",
        }

        stage = ExplainabilityStage()
        result = stage.process(stage_results, fusion_result)

        assert result["success"] is True
        assert "summary" in result
        assert "reasoning_chain" in result
        assert len(result["reasoning_chain"]) > 0


class TestGetPipeline:
    """Test pipeline singleton."""

    def test_get_pipeline_returns_instance(self):
        """Test get_pipeline returns instance."""
        pipeline = get_pipeline()
        assert pipeline is not None
        assert isinstance(pipeline, DetectionPipeline)

    def test_get_pipeline_singleton(self):
        """Test get_pipeline returns same instance."""
        pipeline1 = get_pipeline()
        pipeline2 = get_pipeline()
        assert pipeline1 is pipeline2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
