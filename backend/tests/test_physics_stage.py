
import numpy as np
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.detection.stages.physics_analysis import PhysicsAnalysisStage

def test_physics_stage_initialization():
    stage = PhysicsAnalysisStage()
    assert stage is not None
    assert len(stage.registry.list_sensors()) > 0


def test_physics_stage_processing():
    stage = PhysicsAnalysisStage()
    
    # Create dummy audio (1 second of silence)
    sr = 16000
    audio = np.zeros(sr)
    
    result = stage.process(audio)
    
    assert result["success"] is True
    assert "physics_score" in result
    assert "sensor_results" in result
    
    # Note: Sensor names are human-readable strings, not class names
    sensor_name = "Digital Silence Sensor"
    assert sensor_name in result["sensor_results"]
    
    # Silence sensor should fail on perfect silence
    silence_res = result["sensor_results"][sensor_name]
    assert silence_res["passed"] is False

def test_physics_stage_integration():
    """Test that it integrates with the pipeline's expected data flow"""
    stage = PhysicsAnalysisStage()
    sr = 16000
    # Generate random noise 
    # This acts as a "physically impossible" signal for human speech, so it SHOULD be flagged
    audio = np.random.normal(0, 0.1, sr)
    
    result = stage.process(audio)
    
    assert result["success"] is True
    # Noise should fail physics checks (no formants, no breath, bad coherence)
    # So we expect a HIGH risk score (is_spoof=True)
    assert result["is_spoof"] is True
    assert result["physics_score"] > 0.5


def test_physics_stage_prosecution_only_counts(monkeypatch):
    """Ensure only prosecution-category failures raise physics_score."""
    stage = PhysicsAnalysisStage()

    async def fake_analyze_all(audio, sr, sensor_names=None, metrics=None):
        from backend.sensors.base import SensorResult
        return {
            "Defense Sensor": SensorResult(
                sensor_name="Defense Sensor",
                passed=False,
                value=1.0,
                threshold=0.5,
                metadata={"category": "defense"},
            ),
            "Prosecution Sensor": SensorResult(
                sensor_name="Prosecution Sensor",
                passed=False,
                value=1.0,
                threshold=0.5,
                metadata={"category": "prosecution"},
            ),
        }

    monkeypatch.setattr(stage.registry, "analyze_all", fake_analyze_all)

    sr = 16000
    audio = np.zeros(sr)
    result = stage.process(audio)

    # Only prosecution failure should contribute (scaled to 0.6), defense failure should not.
    assert result["physics_score"] == 0.6
