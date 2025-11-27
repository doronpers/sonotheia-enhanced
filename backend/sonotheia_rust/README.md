# Sonotheia Rust Performance Sensors

High-performance audio analysis sensors implemented in Rust with Python bindings.

## Overview

This library provides performance-critical audio sensors for the Sonotheia Enhanced platform:

- **Vacuum Sensor (SFM)**: Source-Filter Model analysis for voice authenticity
- **Phase Sensor (MPC)**: Multi-Phase Coherence detection for synthetic audio
- **Articulation Sensor**: Speech articulation pattern analysis

## Performance

Rust implementation provides 10-100x speedup over pure Python for:
- FFT operations
- Spectral analysis
- Large array processing
- Parallel sensor execution

## Building

```bash
# Install maturin
pip install maturin

# Build with Python bindings
cd backend/sonotheia_rust
maturin develop --release
```

## Usage

```python
from sonotheia_rust import VacuumSensor, PhaseSensor, ArticulationSensor

# Same API as Python sensors
sensor = VacuumSensor()
result = sensor.analyze(audio_data, sample_rate)

print(f"Passed: {result.passed}")
print(f"Value: {result.value}")
print(f"Threshold: {result.threshold}")
```

## Security

- Overflow checks enabled in all builds
- Input validation for all array operations
- No unsafe code by default
- Bounds checking on all slice operations

## Testing

```bash
# Run Rust tests
cargo test

# Run Python integration tests
python -m pytest tests/test_rust_sensors.py
```
