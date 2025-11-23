# Hybrid OOP + Functional Programming Guide

## Overview

This guide documents the hybrid OOP/Functional programming approach used throughout the codebase, combining the strengths of both paradigms for maximum maintainability, testability, and expressiveness.

## Philosophy

**OOP for Structure, FP for Transformation**

- **Use OOP for**: State management, encapsulation, plugin architectures, framework boundaries
- **Use FP for**: Data transformations, pure computations, pipelines, utilities
- **Hybrid for**: Complex systems that benefit from both approaches

---

## Pattern 1: OOP Classes with Functional Methods

### Example: Sensor Base Class (OOP) with Pure Analysis Logic (FP)

```python
# backend/sensors/breath.py - Hybrid approach

from dataclasses import dataclass
from typing import Tuple
import numpy as np
from .base import BaseSensor, SensorResult

# Functional helper - pure function, no side effects
def calculate_phonation_segments(
    audio_data: np.ndarray,
    samplerate: int,
    silence_threshold_db: float = -60.0,
    frame_duration: float = 0.02
) -> Tuple[float, int]:
    """
    Pure function: Calculate phonation duration from audio data.
    
    Args:
        audio_data: Input signal
        samplerate: Sample rate
        silence_threshold_db: Silence threshold in dB
        frame_duration: Frame size in seconds
    
    Returns:
        (max_phonation_duration, segment_count)
    """
    if len(audio_data) == 0:
        return 0.0, 0
    
    # Convert to dB (functional transformation)
    energy = audio_data ** 2
    db = 10 * np.log10(energy + 1e-10)
    
    # Identify speech frames (functional filter)
    is_speech = db > silence_threshold_db
    
    # Calculate segments (functional reduce)
    segments = []
    current_duration = 0.0
    
    for frame in is_speech:
        if frame:
            current_duration += frame_duration
        elif current_duration > 0:
            segments.append(current_duration)
            current_duration = 0.0
    
    if current_duration > 0:
        segments.append(current_duration)
    
    max_duration = max(segments) if segments else 0.0
    return max_duration, len(segments)


# OOP class - encapsulates behavior and state
class BreathSensor(BaseSensor):
    """
    OOP: Encapsulates sensor configuration and lifecycle.
    FP: Delegates computation to pure functions.
    """
    
    def __init__(
        self,
        max_phonation_seconds: float = 14.0,
        silence_threshold_db: float = -60.0
    ):
        super().__init__(name="breath")
        self._max_phonation = max_phonation_seconds
        self._silence_threshold = silence_threshold_db
    
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Hybrid method:
        - OOP: Instance method with access to configuration
        - FP: Delegates to pure function for computation
        """
        # Use functional helper for computation
        max_phonation, _ = calculate_phonation_segments(
            audio_data,
            samplerate,
            self._silence_threshold
        )
        
        # OOP: Build result object with instance state
        passed = max_phonation <= self._max_phonation
        
        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=round(max_phonation, 2),
            threshold=self._max_phonation,
            reason="BIOLOGICALLY_IMPOSSIBLE" if not passed else None,
            detail=self._build_detail(max_phonation, passed)
        )
    
    def _build_detail(self, phonation: float, passed: bool) -> str:
        """Private method - OOP encapsulation"""
        if not passed:
            return (
                f"Continuous phonation of {phonation:.1f}s exceeds "
                f"biological limit of {self._max_phonation}s"
            )
        return f"Max phonation: {phonation:.1f}s"
```

**Benefits**:
- ✅ Pure functions are easily testable
- ✅ OOP provides clear API boundaries
- ✅ Configuration is encapsulated
- ✅ Computation logic is reusable outside class context

---

## Pattern 2: Functional Composition with OOP Registry

### Example: Sensor Registry

```python
# backend/sensors/registry.py

from typing import List, Dict, Callable, Optional
from functools import reduce
import numpy as np
from .base import BaseSensor, SensorResult

# Functional type definitions
SensorFunction = Callable[[np.ndarray, int], SensorResult]
VerdictAggregator = Callable[[Dict[str, SensorResult]], Tuple[str, str]]


class SensorRegistry:
    """
    Hybrid: OOP for state management, FP for data flow.
    """
    
    def __init__(self):
        self._sensors: Dict[str, BaseSensor] = {}
        self._sensor_order: List[str] = []
    
    def register(self, sensor: BaseSensor, name: Optional[str] = None) -> 'SensorRegistry':
        """
        Fluent interface (OOP) for chainable registration.
        Returns self for method chaining.
        """
        sensor_name = name or sensor.name
        self._sensors[sensor_name] = sensor
        if sensor_name not in self._sensor_order:
            self._sensor_order.append(sensor_name)
        return self  # Fluent interface
    
    def analyze_all(
        self,
        audio_data: np.ndarray,
        samplerate: int,
        sensor_names: Optional[List[str]] = None
    ) -> Dict[str, SensorResult]:
        """
        Hybrid approach:
        - OOP: Method on registry instance
        - FP: Functional map over sensors
        """
        sensors_to_run = sensor_names or self._sensor_order
        
        # Functional approach: map sensors to results
        return {
            name: self._safe_analyze(name, audio_data, samplerate)
            for name in sensors_to_run
            if name in self._sensors
        }
    
    def _safe_analyze(
        self,
        name: str,
        audio_data: np.ndarray,
        samplerate: int
    ) -> SensorResult:
        """
        Error handling wrapper - keeps pure functions safe.
        """
        try:
            sensor = self._sensors[name]
            return sensor.analyze(audio_data, samplerate)
        except Exception as e:
            return SensorResult(
                sensor_name=name,
                passed=None,
                value=0.0,
                threshold=0.0,
                reason="ERROR",
                detail=f"Sensor analysis failed: {str(e)}"
            )
    
    def get_verdict(
        self,
        results: Dict[str, SensorResult],
        fail_on_any: bool = True,
        aggregator: Optional[VerdictAggregator] = None
    ) -> Tuple[str, str]:
        """
        Hybrid verdict calculation:
        - Accepts custom aggregator function (FP)
        - Falls back to default logic (OOP)
        """
        if aggregator:
            return aggregator(results)
        
        return self._default_verdict_logic(results, fail_on_any)
    
    def _default_verdict_logic(
        self,
        results: Dict[str, SensorResult],
        fail_on_any: bool
    ) -> Tuple[str, str]:
        """
        Functional reduce pattern for verdict aggregation.
        """
        # Filter to only pass/fail sensors (functional filter)
        pass_fail_results = {
            name: result
            for name, result in results.items()
            if result.passed is not None
        }
        
        if not pass_fail_results:
            return "UNKNOWN", "No sensor results available"
        
        # Functional reduce to find failures
        failures = [
            (name, result)
            for name, result in pass_fail_results.items()
            if not result.passed
        ]
        
        if failures and fail_on_any:
            name, result = failures[0]
            verdict = result.reason or "SYNTHETIC"
            detail = result.detail or f"{name} failed validation"
            return verdict, detail
        
        return "REAL", "All physics checks passed."
```

**Usage with Method Chaining (Fluent Interface)**:
```python
# OOP fluent interface + FP data flow
registry = (SensorRegistry()
    .register(BreathSensor(), "breath")
    .register(DynamicRangeSensor(), "dynamic_range")
    .register(BandwidthSensor(), "bandwidth"))

# Functional pipeline
results = registry.analyze_all(audio_data, samplerate)
verdict, detail = registry.get_verdict(results)
```

---

## Pattern 3: Functional Data Transformations with OOP Context

### Example: Metrics Collection

```python
# backend/main.py - MetricsCollector

from collections import defaultdict, deque
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
import threading
import time

@dataclass
class MetricSnapshot:
    """Immutable snapshot (FP) of metrics at a point in time"""
    timestamp: float
    requests_total: int
    errors_total: int
    avg_processing_time: float
    
    @property
    def error_rate(self) -> float:
        """Computed property - functional transformation"""
        return self.errors_total / self.requests_total if self.requests_total > 0 else 0.0


class MetricsCollector:
    """
    Hybrid: OOP for thread-safe state, FP for transformations.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        # Mutable state (OOP) protected by lock
        self._request_count = 0
        self._error_count = 0
        self._processing_times = deque(maxlen=1000)
        self._start_time = time.time()
    
    def record_request(self) -> None:
        """OOP: Mutating method with encapsulation"""
        with self._lock:
            self._request_count += 1
    
    def get_snapshot(self) -> MetricSnapshot:
        """
        Returns immutable snapshot (FP) of current state.
        Thread-safe read.
        """
        with self._lock:
            return MetricSnapshot(
                timestamp=time.time(),
                requests_total=self._request_count,
                errors_total=self._error_count,
                avg_processing_time=self._calculate_avg_time()
            )
    
    def _calculate_avg_time(self) -> float:
        """Pure function for calculation"""
        times = list(self._processing_times)
        return sum(times) / len(times) if times else 0.0
    
    # Functional transformation pipeline
    def get_stats(self) -> Dict[str, Any]:
        """
        Functional pipeline: snapshot → transform → dict
        """
        snapshot = self.get_snapshot()
        
        return {
            'requests': {
                'total': snapshot.requests_total,
                'errors': snapshot.errors_total,
                'error_rate': snapshot.error_rate
            },
            'processing': {
                'avg_time_seconds': round(snapshot.avg_processing_time, 3)
            },
            'uptime_seconds': round(snapshot.timestamp - self._start_time, 2)
        }
    
    def apply_transformations(
        self,
        transformers: List[Callable[[MetricSnapshot], Dict]]
    ) -> List[Dict]:
        """
        Functional approach: Apply list of transformations.
        """
        snapshot = self.get_snapshot()
        return [transformer(snapshot) for transformer in transformers]
```

**Usage**:
```python
# Create collector (OOP)
metrics = MetricsCollector()

# Record events (OOP mutation)
metrics.record_request()

# Get immutable snapshot (FP)
snapshot = metrics.get_snapshot()

# Functional transformations
def to_prometheus(snapshot: MetricSnapshot) -> Dict:
    return {
        'sonotheia_requests_total': snapshot.requests_total,
        'sonotheia_error_rate': snapshot.error_rate
    }

def to_json(snapshot: MetricSnapshot) -> Dict:
    return {
        'total': snapshot.requests_total,
        'errorRate': snapshot.error_rate
    }

# Apply multiple transformations functionally
results = metrics.apply_transformations([to_prometheus, to_json])
```

---

## Pattern 4: Functional Utilities with Type Safety

### Example: NumPy Type Conversion

```python
# backend/main.py - Pure functional utility

from typing import Any, Union, Dict, List
import numpy as np

# Type aliases for clarity
JSONValue = Union[None, bool, int, float, str, List['JSONValue'], Dict[str, 'JSONValue']]


def convert_numpy_types(obj: Any) -> JSONValue:
    """
    Pure functional transformation: numpy → JSON-serializable types.
    
    Immutable - doesn't modify input.
    Recursive - functional pattern.
    Type-safe with type hints.
    """
    # Pattern matching style (functional)
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    elif isinstance(obj, dict):
        # Functional map over dict
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        # Functional map over sequence
        return [convert_numpy_types(item) for item in obj]
    
    else:
        return obj


# Functional composition
def compose(*functions):
    """
    Functional composition: compose(f, g, h)(x) = f(g(h(x)))
    """
    def compose_two(f, g):
        return lambda x: f(g(x))
    
    from functools import reduce
    return reduce(compose_two, functions, lambda x: x)


# Usage with composition
def validate_range(value: float) -> float:
    """Pure function: range validation"""
    return max(0.0, min(1.0, value))


def round_value(decimals: int):
    """Higher-order function: returns rounding function"""
    def rounder(value: float) -> float:
        return round(value, decimals)
    return rounder


# Compose transformations
normalize_score = compose(
    round_value(3),
    validate_range,
    float
)

# Use it
score = normalize_score("1.234567")  # → 1.0 (clamped and rounded)
```

---

## Pattern 5: React Functional Components with Hooks (FP) + State Management (OOP-like)

### Example: Demo Component

```jsx
// frontend/src/components/Demo.jsx

import { useState, useRef, useCallback, useMemo } from "react";

// Functional component with hooks
const Demo = () => {
  // State hooks (OOP-like state management)
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  
  const inputRef = useRef(null);
  
  // Pure function - functional helper
  const buildApiUrl = (baseUrl, endpoint) => {
    const base = baseUrl?.length > 0 ? baseUrl.replace(/\/$/, "") : "";
    return `${base}${endpoint}`;
  };
  
  // Memoized value (FP optimization)
  const apiEndpoint = useMemo(
    () => buildApiUrl(import.meta.env.VITE_API_BASE_URL, "/api/v2/detect/quick"),
    []
  );
  
  // Pure functional transformation
  const formatEvidence = useCallback((evidence) => {
    // Functional map + filter pattern
    return Object.entries(evidence)
      .filter(([_, value]) => value !== null && value !== undefined)
      .map(([key, value]) => ({
        label: key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
        value: value.detail || JSON.stringify(value),
        status: value.passed === false ? "fail" : "pass"
      }));
  }, []);
  
  // Async function with state mutations
  const handleFiles = useCallback(async (files) => {
    const file = files?.[0];
    if (!file) return;
    
    // State transitions (OOP-like)
    setUploading(true);
    setResult(null);
    setError("");
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await fetch(apiEndpoint, {
        method: "POST",
        body: formData
      });
      
      // Functional transformation pipeline
      const contentType = response.headers.get("content-type");
      const isJson = contentType?.includes("application/json");
      const payload = isJson ? await response.json() : await response.text();
      
      if (!response.ok) {
        throw new Error(isJson && payload?.detail ? payload.detail : payload);
      }
      
      // Update state with result
      setResult(payload);
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setUploading(false);
    }
  }, [apiEndpoint]);
  
  // Pure render function
  const renderUploadArea = () => (
    <UploadArea
      isDragging={isDragging}
      onDragStateChange={setIsDragging}
      onFileSelect={handleFiles}
    />
  );
  
  const renderResults = () => (
    <ResultsDisplay
      result={result}
      evidence={formatEvidence(result.evidence)}
      onReset={() => setResult(null)}
    />
  );
  
  // Declarative JSX (functional)
  return (
    <section className="demo">
      <div className="demo-container">
        {!uploading && !result && !error && renderUploadArea()}
        {uploading && <LoadingSpinner />}
        {error && <ErrorDisplay error={error} onReset={() => setError("")} />}
        {result && renderResults()}
      </div>
    </section>
  );
};

export default Demo;
```

---

## Pattern 6: Functional Pipeline with OOP Error Handling

### Example: FastAPI Endpoint

```python
# backend/main.py - API endpoint

from typing import Dict, Any
from fastapi import FastAPI, UploadFile, HTTPException
import numpy as np

app = FastAPI()

# Pure functions for data transformation
def validate_audio_data(audio_data: np.ndarray, samplerate: int) -> None:
    """Pure validation - raises on invalid data"""
    if len(audio_data) == 0:
        raise ValueError("Empty audio data")
    if samplerate < 8000 or samplerate > 192000:
        raise ValueError(f"Invalid samplerate: {samplerate}")


def preprocess_audio(audio_data: np.ndarray) -> np.ndarray:
    """Pure function: audio preprocessing"""
    # Convert to mono if stereo
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Ensure float32
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)
    
    return audio_data


def build_response(
    sensor_results: Dict[str, Any],
    verdict: str,
    detail: str,
    processing_time: float
) -> Dict[str, Any]:
    """Pure function: response builder"""
    return {
        "verdict": verdict,
        "detail": detail,
        "processing_time_seconds": processing_time,
        "model_version": "aegis_deterministic_v9.0",
        "evidence": sensor_results
    }


# OOP endpoint with functional pipeline
@app.post("/api/v2/detect/quick")
async def quick_detect(file: UploadFile) -> Dict[str, Any]:
    """
    Hybrid endpoint:
    - OOP: FastAPI framework, exception handling
    - FP: Functional transformation pipeline
    """
    import time
    start_time = time.time()
    
    try:
        # Functional pipeline
        file_content = await file.read()
        audio_data, samplerate = read_audio(file_content)  # IO operation
        
        # Pure transformations
        validate_audio_data(audio_data, samplerate)
        processed_audio = preprocess_audio(audio_data)
        
        # OOP sensor analysis
        sensor_results = sensor_registry.analyze_all(processed_audio, samplerate)
        verdict, detail = sensor_registry.get_verdict(sensor_results)
        
        # Pure response building
        processing_time = time.time() - start_time
        response = build_response(sensor_results, verdict, detail, processing_time)
        
        # Pure type conversion for JSON
        return convert_numpy_types(response)
        
    except ValueError as e:
        # OOP exception handling
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Best Practices Summary

### When to Use OOP

✅ **State management**: Classes for mutable state with encapsulation
✅ **Plugin architectures**: Base classes for extensibility
✅ **Framework boundaries**: FastAPI, React components
✅ **Complex lifecycle**: Initialization, cleanup, context managers
✅ **Inheritance hierarchies**: When true IS-A relationships exist

### When to Use FP

✅ **Data transformations**: Pure functions for computations
✅ **Pipelines**: Composable functions for data flow
✅ **Utilities**: Stateless helpers
✅ **Immutable data**: When state doesn't change
✅ **Concurrency**: Pure functions are thread-safe

### Hybrid Patterns

✅ **OOP classes with pure methods**: State + behavior separation
✅ **Functional composition in OOP**: Registry with functional aggregators
✅ **Immutable snapshots from mutable state**: MetricsCollector pattern
✅ **React hooks**: Functional components with stateful behavior
✅ **Type-safe transformations**: Type hints + pure functions

---

## Testing Hybrid Code

### Test Pure Functions Easily
```python
def test_convert_numpy_types():
    # Pure function - easy to test
    assert convert_numpy_types(np.int64(42)) == 42
    assert convert_numpy_types(np.array([1, 2, 3])) == [1, 2, 3]
```

### Mock OOP Dependencies
```python
def test_sensor_with_mock():
    sensor = BreathSensor()
    # Test pure analyze logic
    result = sensor.analyze(test_audio, 16000)
    assert isinstance(result, SensorResult)
```

### Test Hybrid Components
```python
def test_registry_with_functional_aggregator():
    registry = SensorRegistry()
    
    # Custom aggregator (FP)
    def custom_verdict(results):
        failures = sum(1 for r in results.values() if not r.passed)
        return ("SUSPICIOUS", f"{failures} sensors failed") if failures > 0 else ("REAL", "OK")
    
    # Use functional aggregator with OOP registry
    verdict, detail = registry.get_verdict(results, aggregator=custom_verdict)
```

---

## Advantages of Hybrid Approach

1. **Flexibility**: Choose the right tool for each problem
2. **Testability**: Pure functions are trivial to test
3. **Maintainability**: Clear boundaries between state and logic
4. **Performance**: FP enables optimization (memoization, parallelization)
5. **Type Safety**: Strong typing in both paradigms
6. **Composability**: Functions compose, objects encapsulate

## Conclusion

The hybrid OOP/FP approach provides:
- **Best of both worlds**: Structure from OOP, purity from FP
- **Clear patterns**: Know when to use each paradigm
- **Production-ready**: Battle-tested in real-world applications
- **Modern Python/JavaScript**: Leverages latest language features

This is the recommended approach for building scalable, maintainable systems.
