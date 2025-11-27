"""
Tests for Rust sensor bindings.

These tests verify the Python bindings for the Rust performance sensors.
Requires building the Rust library first with: maturin develop --release
"""

import pytest
import numpy as np

# Try to import the Rust module, skip tests if not available
try:
    from sonotheia_rust import VacuumSensor, PhaseSensor, ArticulationSensor, SensorResult
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust sensors not built")
class TestRustSensorResult:
    """Test the SensorResult class"""

    def test_create_sensor_result(self):
        """Test creating a SensorResult"""
        result = SensorResult(
            sensor_name="test_sensor",
            passed=True,
            value=0.95,
            threshold=0.8,
            reason=None,
            detail="Test passed"
        )
        
        assert result.sensor_name == "test_sensor"
        assert result.passed is True
        assert abs(result.value - 0.95) < 1e-10
        assert abs(result.threshold - 0.8) < 1e-10
        assert result.detail == "Test passed"

    def test_is_pass_method(self):
        """Test the is_pass method"""
        result_pass = SensorResult("test", True, 0.9, 0.8, None, None)
        result_fail = SensorResult("test", False, 0.5, 0.8, None, None)
        
        assert result_pass.is_pass() is True
        assert result_fail.is_pass() is False

    def test_repr(self):
        """Test string representation"""
        result = SensorResult("test", True, 0.9, 0.8, None, None)
        repr_str = repr(result)
        
        assert "test" in repr_str
        assert "PASS" in repr_str


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust sensors not built")
class TestVacuumSensor:
    """Test the VacuumSensor class"""

    def test_create_default(self):
        """Test creating sensor with default threshold"""
        sensor = VacuumSensor()
        
        assert sensor.name == "vacuum_sensor"
        assert 0.0 <= sensor.threshold <= 1.0

    def test_create_custom_threshold(self):
        """Test creating sensor with custom threshold"""
        sensor = VacuumSensor(threshold=0.8)
        
        assert abs(sensor.threshold - 0.8) < 1e-10

    def test_threshold_clamping(self):
        """Test that threshold is clamped to valid range"""
        sensor_high = VacuumSensor(threshold=1.5)
        sensor_low = VacuumSensor(threshold=-0.5)
        
        assert abs(sensor_high.threshold - 1.0) < 1e-10
        assert abs(sensor_low.threshold - 0.0) < 1e-10

    def test_analyze_valid_audio(self):
        """Test analyzing valid audio data"""
        sensor = VacuumSensor()
        
        # Generate test audio (1 second at 16kHz)
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5  # 440 Hz sine wave
        
        result = sensor.analyze(audio, sample_rate)
        
        assert isinstance(result, SensorResult)
        assert result.sensor_name == "vacuum_sensor"
        assert 0.0 <= result.value <= 1.0
        assert result.passed is not None

    def test_analyze_empty_audio(self):
        """Test analyzing empty audio fails validation"""
        sensor = VacuumSensor()
        
        audio = np.array([], dtype=np.float64)
        result = sensor.analyze(audio, 16000)
        
        assert result.passed is False
        assert result.reason is not None

    def test_analyze_invalid_sample_rate(self):
        """Test analyzing with invalid sample rate"""
        sensor = VacuumSensor()
        
        audio = np.random.randn(1000)
        result = sensor.analyze(audio, 100)  # Too low
        
        assert result.passed is False
        assert "validation" in result.detail.lower() or "error" in result.detail.lower()


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust sensors not built")
class TestPhaseSensor:
    """Test the PhaseSensor class"""

    def test_create_default(self):
        """Test creating sensor with default threshold"""
        sensor = PhaseSensor()
        
        assert sensor.name == "phase_sensor"
        assert 0.0 <= sensor.threshold <= 1.0

    def test_create_custom_threshold(self):
        """Test creating sensor with custom threshold"""
        sensor = PhaseSensor(threshold=0.7)
        
        assert abs(sensor.threshold - 0.7) < 1e-10

    def test_analyze_valid_audio(self):
        """Test analyzing valid audio data"""
        sensor = PhaseSensor()
        
        # Generate test audio (1 second at 16kHz)
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Multi-harmonic signal for phase analysis
        audio = (np.sin(2 * np.pi * 200 * t) + 
                 0.5 * np.sin(2 * np.pi * 400 * t) +
                 0.25 * np.sin(2 * np.pi * 600 * t)) * 0.3
        
        result = sensor.analyze(audio, sample_rate)
        
        assert isinstance(result, SensorResult)
        assert result.sensor_name == "phase_sensor"
        assert 0.0 <= result.value <= 1.0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust sensors not built")
class TestArticulationSensor:
    """Test the ArticulationSensor class"""

    def test_create_default(self):
        """Test creating sensor with default threshold"""
        sensor = ArticulationSensor()
        
        assert sensor.name == "articulation_sensor"
        assert 0.0 <= sensor.threshold <= 1.0

    def test_create_custom_threshold(self):
        """Test creating sensor with custom threshold"""
        sensor = ArticulationSensor(threshold=0.5)
        
        assert abs(sensor.threshold - 0.5) < 1e-10

    def test_analyze_valid_audio(self):
        """Test analyzing valid audio data"""
        sensor = ArticulationSensor()
        
        # Generate more complex test audio
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Varying frequency to simulate articulation
        freq = 200 + 100 * np.sin(2 * np.pi * 2 * t)  # Frequency varies between 100-300 Hz
        audio = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate) * 0.5
        
        result = sensor.analyze(audio, sample_rate)
        
        assert isinstance(result, SensorResult)
        assert result.sensor_name == "articulation_sensor"
        assert 0.0 <= result.value <= 1.0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust sensors not built")
class TestPerformance:
    """Test performance characteristics"""

    def test_large_audio_processing(self):
        """Test processing larger audio files"""
        sensor = VacuumSensor()
        
        # Generate 10 seconds of audio at 16kHz
        sample_rate = 16000
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5
        
        import time
        start = time.time()
        result = sensor.analyze(audio, sample_rate)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0, f"Processing took {elapsed:.2f}s, expected < 1.0s"
        assert isinstance(result, SensorResult)

    def test_multiple_sensor_processing(self):
        """Test running multiple sensors"""
        sensors = [VacuumSensor(), PhaseSensor(), ArticulationSensor()]
        
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5
        
        results = []
        for sensor in sensors:
            result = sensor.analyze(audio, sample_rate)
            results.append(result)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, SensorResult)
            assert 0.0 <= result.value <= 1.0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust sensors not built")
class TestSecurityValidation:
    """Test security-related input validation"""

    def test_nan_values(self):
        """Test handling of NaN values in audio"""
        sensor = VacuumSensor()
        
        audio = np.array([0.1, 0.2, np.nan, 0.4, 0.5] + [0.1] * 100)
        result = sensor.analyze(audio, 16000)
        
        assert result.passed is False
        assert "nan" in result.detail.lower() or "validation" in result.detail.lower()

    def test_infinite_values(self):
        """Test handling of infinite values in audio"""
        sensor = VacuumSensor()
        
        audio = np.array([0.1, 0.2, np.inf, 0.4, 0.5] + [0.1] * 100)
        result = sensor.analyze(audio, 16000)
        
        assert result.passed is False

    def test_very_large_values(self):
        """Test handling of very large values"""
        sensor = VacuumSensor()
        
        # Large but not infinite
        audio = np.array([1e308] * 1000)
        result = sensor.analyze(audio, 16000)
        
        # Should handle without crashing
        assert isinstance(result, SensorResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
