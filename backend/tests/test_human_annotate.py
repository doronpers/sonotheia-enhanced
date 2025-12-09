"""
Tests for human annotation tool detection pipeline and file organization.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.human_annotate import (
    HumanAnnotation,
    run_detection,
    save_annotation,
    organize_calibration_dataset,
    ARTIFACT_TYPES
)


class TestHumanAnnotation:
    """Test HumanAnnotation dataclass."""
    
    def test_annotation_creation(self):
        """Test creating a human annotation."""
        annotation = HumanAnnotation(
            audio_file="test.wav",
            timestamp="2023-01-01T00:00:00",
            human_verdict="REAL",
            confidence="HIGH",
            artifacts_heard=["hard_attack"],
            artifact_timestamps={"hard_attack": "0:02-0:05"},
            algorithm_verdict="SYNTHETIC",
            algorithm_score=0.8,
            agrees_with_algorithm=False,
            disagreement_notes="Algorithm missed natural breath pattern"
        )
        
        assert annotation.human_verdict == "REAL"
        assert annotation.confidence == "HIGH"
        assert len(annotation.artifacts_heard) == 1
        assert annotation.agrees_with_algorithm is False
    
    def test_annotation_to_dict(self):
        """Test converting annotation to dictionary."""
        annotation = HumanAnnotation(
            audio_file="test.wav",
            timestamp="2023-01-01T00:00:00",
            human_verdict="SYNTHETIC",
            confidence="MEDIUM",
            artifacts_heard=["two_mouth", "hard_decay"],
            artifact_timestamps={"two_mouth": "throughout"}
        )
        
        data = asdict(annotation)
        assert data['human_verdict'] == "SYNTHETIC"
        assert len(data['artifacts_heard']) == 2


class TestArtifactTaxonomy:
    """Test artifact taxonomy completeness."""
    
    def test_artifact_types_structure(self):
        """Test that all artifact types have required fields."""
        required_fields = {'description', 'sensor', 'examples'}
        
        for artifact_type, info in ARTIFACT_TYPES.items():
            assert isinstance(info, dict), f"{artifact_type} should be a dict"
            for field in required_fields:
                assert field in info, f"{artifact_type} missing {field}"
            
            # Check types
            assert isinstance(info['description'], str)
            assert isinstance(info['sensor'], str)
            assert isinstance(info['examples'], list)
    
    def test_artifact_types_not_empty(self):
        """Test that artifact taxonomy is not empty."""
        assert len(ARTIFACT_TYPES) > 0
    
    def test_artifact_types_have_descriptions(self):
        """Test that all artifact types have non-empty descriptions."""
        for artifact_type, info in ARTIFACT_TYPES.items():
            assert len(info['description']) > 0, f"{artifact_type} has empty description"
    
    def test_artifact_sensor_mapping(self):
        """Test that sensor names are valid."""
        valid_sensor_patterns = [
            "Sensor", "TwoMouthSensor", "GlottalInertiaSensor", 
            "BreathSensor", "CoarticulationSensor", "PhaseCoherenceSensor",
            "DigitalSilenceSensor", "FormantTrajectorySensor", "unknown"
        ]
        
        for artifact_type, info in ARTIFACT_TYPES.items():
            sensor_name = info['sensor']
            # Should either be a known sensor or "unknown"
            assert any(pattern in sensor_name for pattern in valid_sensor_patterns) or sensor_name == "unknown"


class TestRunDetection:
    """Test detection pipeline initialization."""
    
    def test_run_detection_pipeline_initialization(self, tmp_path):
        """Test that detection pipeline initializes correctly."""
        # Create a mock audio file
        audio_file = tmp_path / "test.wav"
        
        with patch('scripts.human_annotate.sf') as mock_sf:
            with patch('scripts.human_annotate.np') as mock_np:
                with patch('scripts.human_annotate.get_default_sensors') as mock_sensors:
                    with patch('scripts.human_annotate.SensorRegistry') as mock_registry:
                        with patch('scripts.human_annotate.calculate_fusion_verdict') as mock_fusion:
                            # Mock audio loading
                            mock_sf.read.return_value = (Mock(), 16000)
                            mock_np.float32 = float
                            
                            # Mock sensors
                            mock_sensor = Mock()
                            mock_sensor.name = "TestSensor"
                            mock_sensors.return_value = [mock_sensor]
                            
                            # Mock registry
                            registry_instance = Mock()
                            registry_instance.list_sensors.return_value = ["TestSensor"]
                            registry_instance.get_sensor.return_value = mock_sensor
                            mock_registry.return_value = registry_instance
                            
                            # Mock sensor result
                            mock_result = Mock()
                            mock_result.passed = True
                            mock_result.value = 0.2
                            mock_result.threshold = 0.5
                            mock_result.detail = "Test detail"
                            mock_result.metadata = {}
                            mock_sensor.analyze.return_value = mock_result
                            
                            # Mock fusion
                            mock_fusion.return_value = {
                                "verdict": "REAL",
                                "global_risk_score": 0.2
                            }
                            
                            result = run_detection(str(audio_file))
                            
                            # Verify pipeline was initialized
                            mock_sensors.assert_called_once()
                            mock_registry.assert_called_once()
                            mock_fusion.assert_called_once()
                            
                            assert result["verdict"] == "REAL"
                            assert result["score"] == 0.2
    
    def test_run_detection_sensor_registry_loading(self, tmp_path):
        """Test that sensors are properly registered."""
        audio_file = tmp_path / "test.wav"
        
        with patch('scripts.human_annotate.sf') as mock_sf:
            with patch('scripts.human_annotate.np'):
                with patch('scripts.human_annotate.get_default_sensors') as mock_sensors:
                    with patch('scripts.human_annotate.SensorRegistry') as mock_registry:
                        with patch('scripts.human_annotate.calculate_fusion_verdict'):
                            mock_sf.read.return_value = (Mock(), 16000)
                            
                            # Create multiple mock sensors
                            sensor1 = Mock()
                            sensor1.name = "Sensor1"
                            sensor2 = Mock()
                            sensor2.name = "Sensor2"
                            mock_sensors.return_value = [sensor1, sensor2]
                            
                            registry_instance = Mock()
                            mock_registry.return_value = registry_instance
                            
                            run_detection(str(audio_file))
                            
                            # Verify all sensors were registered
                            assert registry_instance.register.call_count == 2
    
    def test_run_detection_handles_sensor_failures(self, tmp_path):
        """Test that detection handles individual sensor failures gracefully."""
        audio_file = tmp_path / "test.wav"
        
        with patch('scripts.human_annotate.sf') as mock_sf:
            with patch('scripts.human_annotate.np'):
                with patch('scripts.human_annotate.get_default_sensors') as mock_sensors:
                    with patch('scripts.human_annotate.SensorRegistry') as mock_registry:
                        with patch('scripts.human_annotate.calculate_fusion_verdict') as mock_fusion:
                            mock_sf.read.return_value = (Mock(), 16000)
                            
                            # Mock sensors where one fails
                            good_sensor = Mock()
                            good_sensor.name = "GoodSensor"
                            good_result = Mock()
                            good_result.passed = True
                            good_result.value = 0.1
                            good_result.threshold = 0.5
                            good_result.detail = "OK"
                            good_result.metadata = {}
                            good_sensor.analyze.return_value = good_result
                            
                            bad_sensor = Mock()
                            bad_sensor.name = "BadSensor"
                            bad_sensor.analyze.side_effect = Exception("Sensor failed")
                            
                            mock_sensors.return_value = [good_sensor, bad_sensor]
                            
                            registry_instance = Mock()
                            registry_instance.list_sensors.return_value = ["GoodSensor", "BadSensor"]
                            registry_instance.get_sensor.side_effect = lambda name: {
                                "GoodSensor": good_sensor,
                                "BadSensor": bad_sensor
                            }[name]
                            mock_registry.return_value = registry_instance
                            
                            mock_fusion.return_value = {
                                "verdict": "REAL",
                                "global_risk_score": 0.1
                            }
                            
                            result = run_detection(str(audio_file))
                            
                            # Should still succeed despite one sensor failing
                            assert result["verdict"] == "REAL"
                            assert "GoodSensor" in result["sensors"]
                            assert "BadSensor" in result["sensors"]
                            assert "error" in result["sensors"]["BadSensor"]
    
    def test_run_detection_handles_complete_failure(self, tmp_path):
        """Test that detection handles complete pipeline failure."""
        audio_file = tmp_path / "test.wav"
        
        with patch('scripts.human_annotate.sf') as mock_sf:
            # Mock audio loading failure
            mock_sf.read.side_effect = Exception("Audio load failed")
            
            result = run_detection(str(audio_file))
            
            assert result["verdict"] == "ERROR"
            assert result["score"] == 0.0
            assert "error" in result


class TestSaveAnnotation:
    """Test annotation saving functionality."""
    
    def test_save_annotation_creates_file(self, tmp_path):
        """Test that annotation is saved to JSONL file."""
        output_file = tmp_path / "annotations.jsonl"
        
        annotation = HumanAnnotation(
            audio_file="test.wav",
            timestamp="2023-01-01T00:00:00",
            human_verdict="REAL",
            confidence="HIGH",
            artifacts_heard=[],
            artifact_timestamps={}
        )
        
        save_annotation(annotation, str(output_file))
        
        assert output_file.exists()
        
        # Verify JSON format
        with open(output_file, 'r') as f:
            line = f.readline()
            data = json.loads(line)
            assert data['human_verdict'] == "REAL"
    
    def test_save_annotation_appends_to_file(self, tmp_path):
        """Test that annotations are appended to existing file."""
        output_file = tmp_path / "annotations.jsonl"
        
        annotation1 = HumanAnnotation(
            audio_file="test1.wav",
            timestamp="2023-01-01T00:00:00",
            human_verdict="REAL",
            confidence="HIGH",
            artifacts_heard=[],
            artifact_timestamps={}
        )
        
        annotation2 = HumanAnnotation(
            audio_file="test2.wav",
            timestamp="2023-01-01T00:01:00",
            human_verdict="SYNTHETIC",
            confidence="MEDIUM",
            artifacts_heard=["two_mouth"],
            artifact_timestamps={}
        )
        
        save_annotation(annotation1, str(output_file))
        save_annotation(annotation2, str(output_file))
        
        # Verify both annotations are in file
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            data1 = json.loads(lines[0])
            data2 = json.loads(lines[1])
            assert data1['audio_file'] == "test1.wav"
            assert data2['audio_file'] == "test2.wav"


class TestOrganizeCalibrationDataset:
    """Test file organization for calibration dataset."""
    
    def test_organize_calibration_dataset_real(self, tmp_path):
        """Test organizing REAL verdict files."""
        # Create source audio file
        src_file = tmp_path / "test_real.wav"
        src_file.write_text("fake audio content")
        
        dataset_dir = tmp_path / "calibration"
        
        annotation = HumanAnnotation(
            audio_file=str(src_file),
            timestamp="2023-01-01T00:00:00",
            human_verdict="REAL",
            confidence="HIGH",
            artifacts_heard=[],
            artifact_timestamps={}
        )
        
        organize_calibration_dataset(annotation, str(dataset_dir))
        
        # Verify file was copied to correct directory
        dest_file = dataset_dir / "real" / "test_real.wav"
        assert dest_file.exists()
    
    def test_organize_calibration_dataset_synthetic(self, tmp_path):
        """Test organizing SYNTHETIC verdict files."""
        src_file = tmp_path / "test_synthetic.wav"
        src_file.write_text("fake audio content")
        
        dataset_dir = tmp_path / "calibration"
        
        annotation = HumanAnnotation(
            audio_file=str(src_file),
            timestamp="2023-01-01T00:00:00",
            human_verdict="SYNTHETIC",
            confidence="HIGH",
            artifacts_heard=["two_mouth"],
            artifact_timestamps={}
        )
        
        organize_calibration_dataset(annotation, str(dataset_dir))
        
        dest_file = dataset_dir / "synthetic" / "test_synthetic.wav"
        assert dest_file.exists()
    
    def test_organize_calibration_dataset_unsure(self, tmp_path):
        """Test organizing UNSURE verdict files."""
        src_file = tmp_path / "test_unsure.wav"
        src_file.write_text("fake audio content")
        
        dataset_dir = tmp_path / "calibration"
        
        annotation = HumanAnnotation(
            audio_file=str(src_file),
            timestamp="2023-01-01T00:00:00",
            human_verdict="UNSURE",
            confidence="LOW",
            artifacts_heard=[],
            artifact_timestamps={}
        )
        
        organize_calibration_dataset(annotation, str(dataset_dir))
        
        dest_file = dataset_dir / "unsure" / "test_unsure.wav"
        assert dest_file.exists()
    
    def test_organize_calibration_dataset_skips_duplicates(self, tmp_path):
        """Test that existing files are not overwritten."""
        src_file = tmp_path / "test.wav"
        src_file.write_text("original content")
        
        dataset_dir = tmp_path / "calibration"
        dataset_dir.mkdir()
        (dataset_dir / "real").mkdir()
        
        # Create existing file
        dest_file = dataset_dir / "real" / "test.wav"
        dest_file.write_text("existing content")
        
        annotation = HumanAnnotation(
            audio_file=str(src_file),
            timestamp="2023-01-01T00:00:00",
            human_verdict="REAL",
            confidence="HIGH",
            artifacts_heard=[],
            artifact_timestamps={}
        )
        
        organize_calibration_dataset(annotation, str(dataset_dir))
        
        # Verify existing file was not overwritten
        assert dest_file.read_text() == "existing content"
    
    def test_organize_calibration_dataset_creates_directories(self, tmp_path):
        """Test that verdict directories are created if they don't exist."""
        src_file = tmp_path / "test.wav"
        src_file.write_text("fake audio content")
        
        dataset_dir = tmp_path / "new_calibration"
        
        annotation = HumanAnnotation(
            audio_file=str(src_file),
            timestamp="2023-01-01T00:00:00",
            human_verdict="REAL",
            confidence="HIGH",
            artifacts_heard=[],
            artifact_timestamps={}
        )
        
        organize_calibration_dataset(annotation, str(dataset_dir))
        
        assert (dataset_dir / "real").exists()
        assert (dataset_dir / "real" / "test.wav").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
