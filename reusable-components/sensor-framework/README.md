# Sensor Framework - Reusable Plugin Architecture

## Overview

A flexible, extensible sensor framework for building plugin-based analysis systems. Originally designed for audio authenticity detection but applicable to any domain requiring modular validation/analysis.

## Core Components

### 1. Base Sensor (`base.py`)

**Purpose**: Abstract base class defining the sensor interface

**Key Features**:
- Type-safe with numpy support
- Standardized result structure
- Built-in validation
- JSON serialization

**Usage**:
```python
from sensors.base import BaseSensor, SensorResult

class MySensor(BaseSensor):
    def __init__(self):
        super().__init__(name="my_sensor")
    
    def analyze(self, data, context):
        # Your analysis logic
        return SensorResult(
            sensor_name=self.name,
            passed=True,
            value=0.95,
            threshold=0.8,
            detail="Analysis passed"
        )
```

### 2. Sensor Registry (`registry.py`)

**Purpose**: Centralized sensor management and orchestration

**Key Features**:
- Dynamic registration/unregistration
- Ordered execution
- Error isolation (one sensor failure doesn't stop others)
- Verdict aggregation

**Usage**:
```python
from sensors.registry import SensorRegistry

registry = SensorRegistry()
registry.register(MySensor(), "my_sensor")
registry.register(AnotherSensor(), "another_sensor")

# Run all sensors
results = registry.analyze_all(data, context)

# Get overall verdict
verdict, detail = registry.get_verdict(results, fail_on_any=True)
```

### 3. SensorResult

**Purpose**: Standardized output structure

**Fields**:
- `sensor_name`: str - Identifier
- `passed`: Optional[bool] - Pass/fail (None for info-only)
- `value`: float - Measured value
- `threshold`: float - Decision threshold
- `reason`: Optional[str] - Failure reason code
- `detail`: Optional[str] - Human-readable explanation
- `metadata`: Optional[Dict] - Additional data

## Design Patterns

### 1. Plugin Architecture
- Sensors are independent, swappable modules
- Register/unregister at runtime
- No modification to core framework needed

### 2. Result Aggregation
- Registry combines multiple sensor results
- Configurable failure policies (`fail_on_any`, consensus, etc.)
- Extensible verdict logic

### 3. Error Handling
- Sensor failures are isolated
- Registry continues with remaining sensors
- Error results are standardized

## Adaptation Guide

### For Image Analysis
```python
class ImageQualitySensor(BaseSensor):
    def analyze(self, image: np.ndarray, context: dict) -> SensorResult:
        # Check resolution, sharpness, etc.
        sharpness_score = calculate_sharpness(image)
        return SensorResult(
            sensor_name="image_quality",
            passed=sharpness_score > 0.5,
            value=sharpness_score,
            threshold=0.5
        )
```

### For Text Analysis
```python
class SpamDetectorSensor(BaseSensor):
    def analyze(self, text: str, context: dict) -> SensorResult:
        spam_score = calculate_spam_likelihood(text)
        return SensorResult(
            sensor_name="spam_detector",
            passed=spam_score < 0.3,
            value=spam_score,
            threshold=0.3
        )
```

### For Security Scanning
```python
class VulnerabilitySensor(BaseSensor):
    def analyze(self, code: str, context: dict) -> SensorResult:
        vulnerabilities = scan_for_vulnerabilities(code)
        return SensorResult(
            sensor_name="vuln_scanner",
            passed=len(vulnerabilities) == 0,
            value=len(vulnerabilities),
            threshold=0,
            metadata={'vulnerabilities': vulnerabilities}
        )
```

## Advantages

1. **Modularity**: Add/remove sensors without changing core code
2. **Testability**: Each sensor can be tested independently
3. **Extensibility**: Easy to add new sensor types
4. **Consistency**: All sensors follow same interface
5. **Observability**: Standardized results for monitoring
6. **Type Safety**: Strong typing with numpy support

## Use Cases

- ✅ Audio/Video authenticity detection
- ✅ Image quality assessment
- ✅ Security vulnerability scanning
- ✅ Data quality validation
- ✅ Content moderation
- ✅ Fraud detection
- ✅ System health monitoring
- ✅ Multi-stage ETL pipelines

## Integration Example

```python
# 1. Create registry
registry = SensorRegistry()

# 2. Register sensors
registry.register(BreathSensor(), "breath")
registry.register(DynamicRangeSensor(), "dynamic_range")
registry.register(BandwidthSensor(), "bandwidth")

# 3. Analyze
results = registry.analyze_all(audio_data, samplerate)

# 4. Get verdict
verdict, detail = registry.get_verdict(results)

# 5. Use results
for name, result in results.items():
    print(f"{name}: {'PASS' if result.passed else 'FAIL'}")
    print(f"  Value: {result.value}, Threshold: {result.threshold}")
```

## Files to Extract

From `backend/sensors/`:
- ✅ `base.py` - Core abstractions
- ✅ `registry.py` - Sensor orchestration
- ✅ `utils.py` - Common utilities
- 📝 Example sensors (breath, dynamic_range, bandwidth)

## License

Reusable under project license.
