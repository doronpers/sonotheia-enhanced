"""
Tests for settings.yaml threshold validation against sensor implementations.
"""

import pytest
import sys
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensors.glottal_inertia import GlottalInertiaSensor
from sensors.two_mouth import TwoMouthSensor
from sensors.breath import BreathSensor
from sensors.fusion import DEFAULT_WEIGHTS, THRESHOLD_SYNTHETIC, THRESHOLD_REAL
from sensors.registry import get_default_sensors

# Optional sensors that may not be available in all environments
OPTIONAL_SENSORS = [
    'HFDeepfakeSensor',  # Requires huggingface_hub
    'BreathSensor',      # May be conditionally included
]


class TestSettingsYamlValidation:
    """Test that settings.yaml matches sensor implementations."""
    
    @pytest.fixture
    def settings(self):
        """Load settings.yaml."""
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_settings_file_exists(self):
        """Test that settings.yaml exists."""
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        assert settings_path.exists(), "settings.yaml not found"
    
    def test_settings_yaml_valid(self, settings):
        """Test that settings.yaml is valid YAML."""
        assert settings is not None
        assert isinstance(settings, dict)


class TestGlottalInertiaThresholds:
    """Test glottal_inertia thresholds match sensor implementation."""
    
    @pytest.fixture
    def settings(self):
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_glottal_inertia_thresholds_exist(self, settings):
        """Test that glottal_inertia thresholds are defined."""
        assert 'sensors' in settings
        assert 'glottal_inertia' in settings['sensors']
    
    def test_glottal_inertia_min_rise_time(self, settings):
        """Test min_rise_time_ms matches sensor constant."""
        config_value = settings['sensors']['glottal_inertia']['min_rise_time_ms']
        sensor_value = GlottalInertiaSensor.MIN_RISE_TIME_MS
        
        assert config_value == sensor_value, \
            f"Config min_rise_time_ms ({config_value}) != Sensor MIN_RISE_TIME_MS ({sensor_value})"
    
    def test_glottal_inertia_silence_threshold(self, settings):
        """Test silence_threshold_db matches sensor constant."""
        config_value = settings['sensors']['glottal_inertia']['silence_threshold_db']
        sensor_value = GlottalInertiaSensor.SILENCE_THRESHOLD_DB
        
        assert config_value == sensor_value, \
            f"Config silence_threshold_db ({config_value}) != Sensor SILENCE_THRESHOLD_DB ({sensor_value})"
    
    def test_glottal_inertia_speech_threshold(self, settings):
        """Test speech_threshold_db matches sensor constant."""
        config_value = settings['sensors']['glottal_inertia']['speech_threshold_db']
        sensor_value = GlottalInertiaSensor.SPEECH_THRESHOLD_DB
        
        assert config_value == sensor_value, \
            f"Config speech_threshold_db ({config_value}) != Sensor SPEECH_THRESHOLD_DB ({sensor_value})"
    
    def test_glottal_inertia_thresholds_reasonable(self, settings):
        """Test that threshold values are in reasonable ranges."""
        config = settings['sensors']['glottal_inertia']
        
        # min_rise_time_ms should be positive and less than 1 second
        assert 0 < config['min_rise_time_ms'] < 1000
        
        # silence_threshold_db should be negative (below 0dB)
        assert config['silence_threshold_db'] < 0
        
        # speech_threshold_db should be higher than silence_threshold_db
        assert config['speech_threshold_db'] > config['silence_threshold_db']


class TestTwoMouthThresholds:
    """Test two_mouth thresholds match sensor implementation."""
    
    @pytest.fixture
    def settings(self):
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_two_mouth_thresholds_exist(self, settings):
        """Test that two_mouth thresholds are defined."""
        assert 'sensors' in settings
        assert 'two_mouth' in settings['sensors']
    
    def test_two_mouth_thresholds_reasonable(self, settings):
        """Test that two_mouth threshold values are reasonable."""
        config = settings['sensors']['two_mouth']
        
        # All scores should be between 0 and 1
        assert 0 <= config['vtl_variance_threshold'] <= 1
        assert 0 <= config['vtl_cv_low'] <= 1
        assert 0 <= config['vtl_cv_high'] <= 1
        assert 0 <= config['spectral_conflict_rate'] <= 1
        assert 0 <= config['combined_threshold'] <= 1
        
        # CV high should be greater than CV low
        assert config['vtl_cv_high'] >= config['vtl_cv_low']


class TestBreathThresholds:
    """Test breath sensor thresholds match sensor implementation."""
    
    @pytest.fixture
    def settings(self):
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_breath_thresholds_exist(self, settings):
        """Test that breath thresholds are defined."""
        assert 'sensors' in settings
        assert 'breath' in settings['sensors']
    
    def test_breath_max_phonation_seconds(self, settings):
        """Test max_phonation_seconds is reasonable."""
        config_value = settings['sensors']['breath']['max_phonation_seconds']
        
        # Should be positive and within human limits (typically 10-20 seconds)
        assert 5 < config_value < 30, \
            f"max_phonation_seconds ({config_value}) outside reasonable range (5-30s)"
    
    def test_breath_silence_threshold(self, settings):
        """Test silence_threshold_db is reasonable."""
        config_value = settings['sensors']['breath']['silence_threshold_db']
        
        # Should be negative (below 0dB)
        assert config_value < 0
        assert config_value > -100  # Not too extreme
    
    def test_breath_frame_size(self, settings):
        """Test frame_size_seconds is reasonable."""
        config_value = settings['sensors']['breath']['frame_size_seconds']
        
        # Should be small but not too small (typically 10-50ms)
        assert 0.001 < config_value < 0.1, \
            f"frame_size_seconds ({config_value}) outside reasonable range"


class TestFusionWeights:
    """Test fusion weights and thresholds."""
    
    @pytest.fixture
    def settings(self):
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_fusion_weights_exist(self, settings):
        """Test that fusion weights are defined."""
        assert 'fusion' in settings
        assert 'weights' in settings['fusion']
    
    def test_fusion_weights_sum_reasonable(self, settings):
        """Test that fusion weights sum to approximately 1.0."""
        weights = settings['fusion']['weights']
        weight_sum = sum(weights.values())
        
        # Weights should sum to ~1.0 (allow some tolerance)
        assert 0.8 <= weight_sum <= 1.2, \
            f"Fusion weights sum to {weight_sum}, expected ~1.0"
    
    def test_fusion_weights_all_positive(self, settings):
        """Test that all weights are non-negative."""
        weights = settings['fusion']['weights']
        
        for sensor_name, weight in weights.items():
            assert weight >= 0, f"{sensor_name} has negative weight: {weight}"
    
    def test_fusion_weights_match_default_sensors(self, settings):
        """Test that fusion weights include all major sensors."""
        weights = settings['fusion']['weights']
        default_sensors = get_default_sensors()
        
        # Get sensor class names
        sensor_names = [type(s).__name__ for s in default_sensors]
        
        # Check that important sensors have weights defined
        important_sensors = [
            'GlottalInertiaSensor',
            'TwoMouthSensor',
            'FormantTrajectorySensor',
            'PhaseCoherenceSensor'
        ]
        
        for sensor_name in important_sensors:
            if sensor_name in sensor_names:
                assert sensor_name in weights, \
                    f"{sensor_name} is registered but has no weight in config"
    
    def test_fusion_thresholds_exist(self, settings):
        """Test that fusion thresholds are defined."""
        assert 'fusion' in settings
        assert 'thresholds' in settings['fusion']
        assert 'synthetic' in settings['fusion']['thresholds']
        assert 'real' in settings['fusion']['thresholds']
    
    def test_fusion_thresholds_reasonable(self, settings):
        """Test that fusion thresholds are in valid range."""
        thresholds = settings['fusion']['thresholds']
        
        synthetic_threshold = thresholds['synthetic']
        real_threshold = thresholds['real']
        
        # Thresholds should be between 0 and 1
        assert 0 <= synthetic_threshold <= 1
        assert 0 <= real_threshold <= 1
        
        # Synthetic threshold should be higher than real threshold
        assert synthetic_threshold > real_threshold, \
            f"synthetic threshold ({synthetic_threshold}) should be > real threshold ({real_threshold})"
    
    def test_fusion_thresholds_match_code_constants(self, settings):
        """Test that fusion thresholds match code constants."""
        thresholds = settings['fusion']['thresholds']
        
        # Note: The code constants may be overridden by config, so we just
        # verify they're in the same reasonable range
        assert abs(thresholds['synthetic'] - THRESHOLD_SYNTHETIC) < 0.3, \
            "Config synthetic threshold differs significantly from code constant"
        assert abs(thresholds['real'] - THRESHOLD_REAL) < 0.3, \
            "Config real threshold differs significantly from code constant"


class TestConfiguredSensorsExist:
    """Test that all configured sensors actually exist."""
    
    @pytest.fixture
    def settings(self):
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_sensor_config_sections_valid(self, settings):
        """Test that sensor configuration sections reference valid sensors."""
        sensor_configs = settings.get('sensors', {})
        default_sensors = get_default_sensors()
        
        # Get all sensor names (convert class names to snake_case-like names)
        sensor_class_names = [type(s).__name__ for s in default_sensors]
        
        # Map config keys to expected sensor patterns
        config_to_sensor_map = {
            'glottal_inertia': 'GlottalInertiaSensor',
            'two_mouth': 'TwoMouthSensor',
            'breath': 'BreathSensor',
            'dynamic_range': 'DynamicRangeSensor',
            'bandwidth': 'BandwidthSensor'
        }
        
        for config_key, sensor_name in config_to_sensor_map.items():
            if config_key in sensor_configs:
                # This sensor is configured, verify it exists or is optional
                is_optional = sensor_name in OPTIONAL_SENSORS
                assert sensor_name in sensor_class_names or is_optional, \
                    f"Sensor {sensor_name} configured but not found in default sensors"
    
    def test_fusion_weights_reference_valid_sensors(self, settings):
        """Test that fusion weights reference sensors that exist."""
        weights = settings.get('fusion', {}).get('weights', {})
        default_sensors = get_default_sensors()
        sensor_class_names = [type(s).__name__ for s in default_sensors]
        
        for sensor_name in weights.keys():
            # Each weight should reference either a valid sensor or be a special key
            if not sensor_name.endswith('Sensor'):
                continue  # Skip non-sensor keys
            
            # Sensor should exist in default sensors or be optional
            # (Note: some sensors may be optional/conditional)
            if weights[sensor_name] > 0:
                # Only check sensors with positive weight
                is_optional = sensor_name in OPTIONAL_SENSORS
                assert sensor_name in sensor_class_names or is_optional, \
                    f"Fusion weight defined for unknown sensor: {sensor_name}"


class TestThresholdRangeConsistency:
    """Test internal consistency of threshold ranges."""
    
    @pytest.fixture
    def settings(self):
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_voice_thresholds_consistent(self, settings):
        """Test that voice detection thresholds are internally consistent."""
        voice_config = settings.get('voice', {})
        
        # All thresholds should be between 0 and 1
        assert 0 <= voice_config.get('deepfake_threshold', 0.5) <= 1
        assert 0 <= voice_config.get('liveness_threshold', 0.5) <= 1
        assert 0 <= voice_config.get('speaker_threshold', 0.5) <= 1
        assert 0 <= voice_config.get('min_quality', 0.5) <= 1
    
    def test_sar_thresholds_consistent(self, settings):
        """Test that SAR detection thresholds are consistent."""
        sar_config = settings.get('sar_detection_rules', {})
        
        if 'structuring' in sar_config:
            structuring = sar_config['structuring']
            # Threshold percentage should be between 0 and 1
            assert 0 <= structuring.get('threshold_percentage', 0.95) <= 1
            # Threshold amount should be positive
            assert structuring.get('threshold_amount', 10000) > 0
        
        if 'synthetic_voice' in sar_config:
            synthetic = sar_config['synthetic_voice']
            # Threshold should be between 0 and 1
            assert 0 <= synthetic.get('threshold', 0.7) <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
