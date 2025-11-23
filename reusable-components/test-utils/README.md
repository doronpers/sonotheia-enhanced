# Test Utilities - Reusable Testing Patterns

## Overview

Collection of reusable test utilities, fixtures, and patterns for comprehensive testing of audio analysis systems (adaptable to other domains).

## Core Testing Patterns

### 1. Test Data Generation

#### Audio File Generator (Hybrid: OOP structure, FP generation)

```python
import io
import numpy as np
import soundfile as sf
from typing import Optional, Literal
from dataclasses import dataclass

@dataclass
class AudioSpec:
    """Immutable audio specification (FP)"""
    duration_seconds: float
    samplerate: int
    num_channels: int = 1
    dtype: str = 'float32'


class AudioGenerator:
    """OOP: Generator with configuration"""
    
    def __init__(self, default_samplerate: int = 16000):
        self._default_samplerate = default_samplerate
    
    @staticmethod
    def sine_wave(
        frequency: float,
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 0.5
    ) -> np.ndarray:
        """Pure function: Generate sine wave"""
        t = np.linspace(
            0, duration_seconds,
            int(duration_seconds * samplerate),
            endpoint=False,
            dtype=np.float32
        )
        return (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    
    @staticmethod
    def white_noise(
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 0.3,
        seed: Optional[int] = None
    ) -> np.ndarray:
        """Pure function: Generate white noise"""
        if seed is not None:
            np.random.seed(seed)
        
        samples = int(duration_seconds * samplerate)
        return (amplitude * np.random.randn(samples)).astype(np.float32)
    
    @staticmethod
    def silence(duration_seconds: float, samplerate: int) -> np.ndarray:
        """Pure function: Generate silence"""
        samples = int(duration_seconds * samplerate)
        return np.zeros(samples, dtype=np.float32)
    
    @staticmethod
    def impulse_train(
        interval_seconds: float,
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 1.0
    ) -> np.ndarray:
        """Pure function: Generate impulse train (for high crest factor)"""
        samples = int(duration_seconds * samplerate)
        interval_samples = int(interval_seconds * samplerate)
        
        audio = np.zeros(samples, dtype=np.float32)
        audio[::interval_samples] = amplitude
        return audio
    
    def to_bytes(
        self,
        audio_data: np.ndarray,
        samplerate: Optional[int] = None,
        format: Literal['wav', 'flac', 'ogg'] = 'wav'
    ) -> io.BytesIO:
        """Convert audio to bytes for upload testing"""
        buffer = io.BytesIO()
        sr = samplerate or self._default_samplerate
        sf.write(buffer, audio_data, sr, format=format)
        buffer.seek(0)
        return buffer
    
    def create_test_audio(
        self,
        spec: AudioSpec,
        signal_type: Literal['sine', 'noise', 'silence', 'impulse'] = 'sine',
        **kwargs
    ) -> np.ndarray:
        """Factory method for test audio generation"""
        generators = {
            'sine': lambda: self.sine_wave(
                kwargs.get('frequency', 440.0),
                spec.duration_seconds,
                spec.samplerate
            ),
            'noise': lambda: self.white_noise(
                spec.duration_seconds,
                spec.samplerate,
                seed=kwargs.get('seed')
            ),
            'silence': lambda: self.silence(
                spec.duration_seconds,
                spec.samplerate
            ),
            'impulse': lambda: self.impulse_train(
                kwargs.get('interval', 0.1),
                spec.duration_seconds,
                spec.samplerate
            )
        }
        
        return generators[signal_type]()
```

**Usage**:
```python
# Create generator
gen = AudioGenerator(samplerate=16000)

# Generate different signals
sine = gen.sine_wave(frequency=440, duration_seconds=1.0, samplerate=16000)
noise = gen.white_noise(duration_seconds=2.0, samplerate=16000, seed=42)
silence = gen.silence(duration_seconds=0.5, samplerate=16000)
impulses = gen.impulse_train(interval_seconds=0.1, duration_seconds=1.0, samplerate=16000)

# Convert to uploadable format
audio_bytes = gen.to_bytes(sine, samplerate=16000, format='wav')
```

---

### 2. Boundary Testing Pattern

```python
from typing import Callable, Any
import pytest

class BoundaryTester:
    """Systematic boundary testing (Hybrid OOP/FP)"""
    
    @staticmethod
    def test_at_threshold(
        test_func: Callable[[float], bool],
        threshold: float,
        should_pass: bool = True,
        tolerance: float = 0.0
    ):
        """
        Pure function: Test exactly at threshold.
        
        Args:
            test_func: Function to test (takes value, returns pass/fail)
            threshold: Threshold value
            should_pass: Expected result at threshold
            tolerance: Floating point tolerance
        """
        result = test_func(threshold + tolerance)
        assert result == should_pass, \
            f"At threshold {threshold}: expected {should_pass}, got {result}"
    
    @staticmethod
    def test_just_below_threshold(
        test_func: Callable[[float], bool],
        threshold: float,
        delta: float = 0.01,
        should_pass: bool = True
    ):
        """Test just below threshold"""
        result = test_func(threshold - delta)
        assert result == should_pass
    
    @staticmethod
    def test_just_above_threshold(
        test_func: Callable[[float], bool],
        threshold: float,
        delta: float = 0.01,
        should_pass: bool = False
    ):
        """Test just above threshold"""
        result = test_func(threshold + delta)
        assert result == should_pass
    
    @classmethod
    def test_all_boundaries(
        cls,
        test_func: Callable[[float], bool],
        threshold: float,
        passes_when_below: bool = True
    ):
        """Run complete boundary test suite"""
        if passes_when_below:
            cls.test_just_below_threshold(test_func, threshold, should_pass=True)
            cls.test_at_threshold(test_func, threshold, should_pass=True)
            cls.test_just_above_threshold(test_func, threshold, should_pass=False)
        else:
            cls.test_just_below_threshold(test_func, threshold, should_pass=False)
            cls.test_at_threshold(test_func, threshold, should_pass=False)
            cls.test_just_above_threshold(test_func, threshold, should_pass=True)
```

**Usage**:
```python
def test_breath_sensor_boundaries():
    MAX_PHONATION = 14.0
    
    def test_phonation(duration):
        sensor = BreathSensor(max_phonation_seconds=MAX_PHONATION)
        audio = gen.sine_wave(440, duration, 16000)
        result = sensor.analyze(audio, 16000)
        return result.passed
    
    # Test all boundary conditions
    BoundaryTester.test_all_boundaries(
        test_phonation,
        threshold=MAX_PHONATION,
        passes_when_below=True
    )
```

---

### 3. Edge Case Testing Pattern

```python
from enum import Enum
from typing import List, Tuple

class EdgeCase(Enum):
    """Enumeration of common edge cases"""
    EMPTY = "empty"
    SINGLE_SAMPLE = "single_sample"
    VERY_SHORT = "very_short"
    VERY_LONG = "very_long"
    ALL_ZEROS = "all_zeros"
    ALL_ONES = "all_ones"
    CONSTANT = "constant"
    ALTERNATING = "alternating"
    DC_OFFSET = "dc_offset"


class EdgeCaseGenerator:
    """Generate edge case test data"""
    
    @staticmethod
    def generate(case: EdgeCase, samplerate: int = 16000) -> np.ndarray:
        """Functional pattern: case mapping"""
        generators = {
            EdgeCase.EMPTY: lambda: np.array([], dtype=np.float32),
            EdgeCase.SINGLE_SAMPLE: lambda: np.array([0.5], dtype=np.float32),
            EdgeCase.VERY_SHORT: lambda: np.ones(10, dtype=np.float32) * 0.5,
            EdgeCase.VERY_LONG: lambda: np.ones(samplerate * 300, dtype=np.float32) * 0.5,
            EdgeCase.ALL_ZEROS: lambda: np.zeros(samplerate, dtype=np.float32),
            EdgeCase.ALL_ONES: lambda: np.ones(samplerate, dtype=np.float32),
            EdgeCase.CONSTANT: lambda: np.full(samplerate, 0.5, dtype=np.float32),
            EdgeCase.ALTERNATING: lambda: np.tile([1.0, -1.0], samplerate // 2).astype(np.float32),
            EdgeCase.DC_OFFSET: lambda: np.ones(samplerate, dtype=np.float32) * 0.5
        }
        
        return generators[case]()
    
    @classmethod
    def all_cases(cls, samplerate: int = 16000) -> List[Tuple[EdgeCase, np.ndarray]]:
        """Generate all edge cases"""
        return [(case, cls.generate(case, samplerate)) for case in EdgeCase]
```

**Usage**:
```python
@pytest.mark.parametrize("case,audio", EdgeCaseGenerator.all_cases())
def test_sensor_handles_edge_cases(case, audio):
    """Test sensor with all edge cases"""
    sensor = MyS ensor()
    result = sensor.analyze(audio, 16000)
    
    # Should not crash
    assert result is not None
    assert isinstance(result, SensorResult)
    assert 'value' in result.to_dict()
```

---

### 4. API Testing Utilities

```python
from fastapi.testclient import TestClient
from typing import Dict, Optional, Union
import io

class APITester:
    """Reusable API testing patterns (Hybrid)"""
    
    def __init__(self, client: TestClient):
        self._client = client
    
    def upload_audio(
        self,
        audio_data: np.ndarray,
        samplerate: int = 16000,
        filename: str = "test.wav",
        format: str = "wav",
        content_type: str = "audio/wav"
    ) -> Dict:
        """
        Upload audio and return response.
        
        Returns parsed JSON response.
        """
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, samplerate, format=format)
        buffer.seek(0)
        
        response = self._client.post(
            "/api/v2/detect/quick",
            files={"file": (filename, buffer, content_type)}
        )
        
        return {
            'status_code': response.status_code,
            'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
            'text': response.text,
            'headers': dict(response.headers)
        }
    
    def assert_success_response(
        self,
        response: Dict,
        expected_fields: Optional[List[str]] = None
    ):
        """Assert successful API response"""
        assert response['status_code'] == 200
        assert response['json'] is not None
        
        if expected_fields:
            for field in expected_fields:
                assert field in response['json'], f"Missing field: {field}"
    
    def assert_error_response(
        self,
        response: Dict,
        expected_status: int,
        expected_message: Optional[str] = None
    ):
        """Assert error response"""
        assert response['status_code'] == expected_status
        
        if expected_message:
            error_text = response['json'].get('detail', '') if response['json'] else response['text']
            assert expected_message.lower() in error_text.lower()
    
    def test_endpoint_with_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ):
        """
        Functional pattern: Run multiple test scenarios.
        
        Each scenario is a dict with:
        - audio: np.ndarray
        - expected_status: int
        - expected_verdict: Optional[str]
        - description: str
        """
        for scenario in scenarios:
            response = self.upload_audio(scenario['audio'])
            
            assert response['status_code'] == scenario['expected_status'], \
                f"Scenario '{scenario['description']}' failed"
            
            if 'expected_verdict' in scenario and response['json']:
                assert response['json']['verdict'] == scenario['expected_verdict']
```

**Usage**:
```python
def test_api_with_scenarios(client):
    tester = APITester(client)
    gen = AudioGenerator()
    
    scenarios = [
        {
            'audio': gen.sine_wave(440, 2.0, 16000),
            'expected_status': 200,
            'expected_verdict': 'REAL',
            'description': 'Normal sine wave'
        },
        {
            'audio': gen.create_test_audio(
                AudioSpec(duration_seconds=20.0, samplerate=16000),
                'sine'
            ),
            'expected_status': 200,
            'expected_verdict': 'SYNTHETIC',
            'description': 'Too long phonation'
        },
        {
            'audio': np.array([]),
            'expected_status': 200,  # Empty audio might be handled
            'description': 'Empty audio'
        }
    ]
    
    tester.test_endpoint_with_scenarios(scenarios)
```

---

### 5. Fixture Patterns (pytest)

```python
import pytest

@pytest.fixture
def audio_generator():
    """Reusable audio generator fixture"""
    return AudioGenerator(default_samplerate=16000)


@pytest.fixture
def test_audio_short(audio_generator):
    """Fixture: Short audio"""
    return audio_generator.sine_wave(440, 1.0, 16000)


@pytest.fixture
def test_audio_long(audio_generator):
    """Fixture: Long audio"""
    return audio_generator.sine_wave(440, 20.0, 16000)


@pytest.fixture
def test_audio_silence(audio_generator):
    """Fixture: Silence"""
    return audio_generator.silence(2.0, 16000)


@pytest.fixture(params=[
    ('sine', {'frequency': 440}),
    ('noise', {'seed': 42}),
    ('silence', {}),
    ('impulse', {'interval': 0.1})
])
def test_audio_parametrized(request, audio_generator):
    """Parametrized fixture for multiple audio types"""
    signal_type, kwargs = request.param
    return audio_generator.create_test_audio(
        AudioSpec(duration_seconds=2.0, samplerate=16000),
        signal_type=signal_type,
        **kwargs
    )


@pytest.fixture
def client():
    """FastAPI test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def api_tester(client):
    """API testing utility"""
    return APITester(client)
```

---

### 6. Assertion Helpers

```python
class AssertHelpers:
    """Reusable assertion patterns"""
    
    @staticmethod
    def assert_sensor_result_valid(result: SensorResult):
        """Assert SensorResult has valid structure"""
        assert hasattr(result, 'sensor_name')
        assert hasattr(result, 'value')
        assert hasattr(result, 'threshold')
        assert isinstance(result.value, (int, float))
        assert isinstance(result.threshold, (int, float))
        
        if result.passed is not None:
            assert isinstance(result.passed, bool)
    
    @staticmethod
    def assert_dict_contains_keys(d: Dict, keys: List[str]):
        """Assert dict contains all specified keys"""
        for key in keys:
            assert key in d, f"Missing key: {key}"
    
    @staticmethod
    def assert_value_in_range(
        value: float,
        min_val: float,
        max_val: float,
        inclusive: bool = True
    ):
        """Assert value is in range"""
        if inclusive:
            assert min_val <= value <= max_val, \
                f"Value {value} not in range [{min_val}, {max_val}]"
        else:
            assert min_val < value < max_val, \
                f"Value {value} not in range ({min_val}, {max_val})"
    
    @staticmethod
    def assert_api_response_structure(response: Dict):
        """Assert API response has expected structure"""
        required_fields = ['verdict', 'detail', 'processing_time_seconds', 'evidence']
        AssertHelpers.assert_dict_contains_keys(response, required_fields)
        
        # Verify types
        assert isinstance(response['verdict'], str)
        assert isinstance(response['detail'], str)
        assert isinstance(response['processing_time_seconds'], (int, float))
        assert isinstance(response['evidence'], dict)
```

---

### 7. Performance Testing Pattern

```python
import time
from typing import Callable

class PerformanceTester:
    """Performance testing utilities"""
    
    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """Measure function execution time"""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    
    @staticmethod
    def assert_execution_time(
        func: Callable,
        max_seconds: float,
        *args,
        **kwargs
    ):
        """Assert function completes within time limit"""
        result, elapsed = PerformanceTester.measure_execution_time(func, *args, **kwargs)
        assert elapsed < max_seconds, \
            f"Execution took {elapsed:.2f}s, expected < {max_seconds}s"
        return result
    
    @staticmethod
    def benchmark(
        func: Callable,
        iterations: int = 100,
        *args,
        **kwargs
    ) -> Dict[str, float]:
        """Benchmark function performance"""
        times = []
        for _ in range(iterations):
            _, elapsed = PerformanceTester.measure_execution_time(func, *args, **kwargs)
            times.append(elapsed)
        
        return {
            'mean': np.mean(times),
            'median': np.median(times),
            'min': np.min(times),
            'max': np.max(times),
            'std': np.std(times)
        }
```

**Usage**:
```python
def test_sensor_performance():
    sensor = BreathSensor()
    audio = gen.white_noise(60.0, 16000)  # 1 minute
    
    # Assert completes in reasonable time
    result = PerformanceTester.assert_execution_time(
        sensor.analyze,
        max_seconds=5.0,
        audio_data=audio,
        samplerate=16000
    )
    
    # Benchmark
    stats = PerformanceTester.benchmark(
        sensor.analyze,
        iterations=10,
        audio_data=audio,
        samplerate=16000
    )
    
    print(f"Mean time: {stats['mean']:.3f}s")
    print(f"Std dev: {stats['std']:.3f}s")
```

---

## Complete Test Example

```python
class TestBreathSensorComplete:
    """Complete test suite using all patterns"""
    
    @pytest.fixture(autouse=True)
    def setup(self, audio_generator):
        self.gen = audio_generator
        self.sensor = BreathSensor()
    
    def test_success_cases(self):
        """Test successful detection"""
        audio = self.gen.sine_wave(440, 5.0, 16000)
        result = self.sensor.analyze(audio, 16000)
        
        AssertHelpers.assert_sensor_result_valid(result)
        assert result.passed is True
    
    def test_boundary_conditions(self):
        """Test all boundary conditions"""
        def test_duration(duration):
            audio = self.gen.sine_wave(440, duration, 16000)
            result = self.sensor.analyze(audio, 16000)
            return result.passed
        
        BoundaryTester.test_all_boundaries(
            test_duration,
            threshold=14.0,
            passes_when_below=True
        )
    
    @pytest.mark.parametrize("case,audio", EdgeCaseGenerator.all_cases())
    def test_edge_cases(self, case, audio):
        """Test all edge cases"""
        result = self.sensor.analyze(audio, 16000)
        AssertHelpers.assert_sensor_result_valid(result)
    
    def test_performance(self):
        """Test performance"""
        audio = self.gen.white_noise(60.0, 16000)
        PerformanceTester.assert_execution_time(
            self.sensor.analyze,
            max_seconds=5.0,
            audio_data=audio,
            samplerate=16000
        )
```

---

## Benefits

✅ **Reusable**: Copy patterns to any project
✅ **Comprehensive**: Covers success, failure, boundary, edge cases
✅ **Maintainable**: Clear, documented patterns
✅ **Hybrid**: OOP structure with FP purity
✅ **Parametrized**: pytest fixtures and parameters
✅ **Performance**: Built-in benchmarking

## License

Reusable under project license.
