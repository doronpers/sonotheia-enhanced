# ProsodicContinuitySensor

A physics-based sensor that detects synthetic or spliced audio by analyzing prosodic continuity in speech.

## Overview

Natural human speech exhibits smooth transitions in prosodic features (pitch, energy, timbre). Synthetic speech and audio splicing often introduce abrupt discontinuities that violate natural speech production constraints. This sensor detects these anomalies.

## Key Features

- ✅ **No librosa dependency** - Uses only numpy + scipy
- ✅ **Physics-based analysis** - No ML models required
- ✅ **VAD integration** - Focuses only on speech segments
- ✅ **Configurable thresholds** - Loaded from settings.yaml
- ✅ **Calibration support** - Learn from organic samples
- ✅ **JSON-safe outputs** - All values are serializable
- ✅ **Category: Prosecution** - Detects fake/synthetic speech

## How It Works

### 1. Speech Segment Detection
Uses `VoiceActivityDetector` to identify speech regions, ignoring silence and non-speech.

### 2. Frame-Level Feature Extraction (25ms frames, 10ms hop)

For each frame:
- **RMS Energy**: Frame amplitude
- **Spectral Centroid**: Brightness/timbre via FFT
- **F0 (Pitch)**: Fundamental frequency via autocorrelation (70-400 Hz)
  - Returns `np.nan` for unvoiced frames

### 3. Delta Computation & Z-Score Normalization

Computes frame-to-frame changes:
- F0 deltas (voiced frames only)
- Energy deltas (all frames)
- Centroid deltas (all frames)

Normalizes via z-scores: `z = (delta - mean) / std`

### 4. Prosodic Break Detection

A "prosodic break" occurs when any z-score exceeds threshold (default: 3.0σ).

### 5. Risk Score Calculation

```
breaks_per_second = total_breaks / total_speech_duration
risk_score = min(1.0, breaks_per_second / max_breaks_per_second)
passed = risk_score < risk_threshold
```

## Configuration

Default settings in `backend/config/settings.yaml`:

```yaml
sensors:
  prosodic_continuity:
    max_breaks_per_second: 2.0     # Maximum natural break rate
    risk_threshold: 0.7            # Risk score threshold for failure
    f0_zscore_threshold: 3.0       # Z-score threshold for pitch breaks
    energy_zscore_threshold: 3.0   # Z-score threshold for energy breaks
    centroid_zscore_threshold: 3.0 # Z-score threshold for timbre breaks
    min_speech_duration: 0.5       # Minimum speech duration for analysis
```

## Usage

### Basic Usage

```python
from backend.sensors.prosodic_continuity import ProsodicContinuitySensor
import numpy as np

sensor = ProsodicContinuitySensor()

# Load or generate audio
audio_data = ...  # numpy array, mono, float32
samplerate = 16000

# Analyze
result = sensor.analyze(audio_data, samplerate)

print(f"Passed: {result.passed}")
print(f"Risk score: {result.value:.3f}")
print(f"Detail: {result.detail}")
print(f"Total breaks: {result.metadata['total_breaks']}")
print(f"Breaks/sec: {result.metadata['breaks_per_second']:.2f}")
```

### With Registry

```python
from backend.sensors import get_default_sensors, SensorRegistry

registry = SensorRegistry()
for sensor in get_default_sensors():
    registry.register(sensor)

sensor = registry.get_sensor('ProsodicContinuitySensor')
result = sensor.analyze(audio_data, samplerate)
```

### Calibration with Organic Samples

```bash
# Run calibration
cd backend/sensors
python calibrate_prosodic.py --organic-dir /path/to/organic/samples --output config.yaml

# Or use the helper script
./example_calibration.sh /path/to/organic/samples
```

See [PROSODIC_CONTINUITY_CALIBRATION.md](PROSODIC_CONTINUITY_CALIBRATION.md) for detailed calibration guide.

## Return Values

### SensorResult Fields

- **passed**: `bool | None`
  - `True`: Natural prosodic continuity detected
  - `False`: Abrupt changes detected (likely synthetic/spliced)
  - `None`: Cannot analyze (no speech, too short, error)

- **value**: `float` - Risk score [0.0, 1.0]
  - 0.0: Very smooth (few breaks)
  - 1.0: Many abrupt changes

- **threshold**: `float` - Risk threshold (default: 0.7)

- **reason**: `str | None`
  - `"PROSODIC_DISCONTINUITY"`: Failed due to breaks
  - `"NO_SPEECH"`: No speech detected
  - `"INSUFFICIENT_SPEECH"`: Too little speech
  - `"INSUFFICIENT_FRAMES"`: Too few frames
  - `"INVALID_INPUT"`: Bad input
  - `"ERROR"`: Analysis error

- **detail**: `str` - Human-readable explanation

- **metadata**: `dict`
  - `total_breaks`: Total number of breaks
  - `breaks_per_second`: Normalized break rate
  - `pitch_breaks`: Breaks from F0 changes
  - `energy_breaks`: Breaks from amplitude changes
  - `centroid_breaks`: Breaks from timbre changes
  - `total_speech_duration`: Total speech time (seconds)
  - `num_speech_segments`: Number of speech segments

## Edge Cases

### Handled Gracefully

1. **No speech detected**: Returns `passed=None`, reason `"NO_SPEECH"`
2. **Too short**: Returns `passed=None`, reason `"INSUFFICIENT_SPEECH"`
3. **Very short signal**: Returns `passed=None`, reason `"INSUFFICIENT_FRAMES"`
4. **Invalid input**: Returns `passed=None`, reason `"INVALID_INPUT"`
5. **Analysis errors**: Returns `passed=None`, reason `"ERROR"`

### When passed=None

The sensor abstains from verdict when:
- Total speech < 0.5s (configurable)
- Signal too short for FFT/autocorrelation
- No speech detected by VAD
- Invalid or corrupted audio

## Fusion Weight

Default fusion weight: **0.10** (10% contribution to global risk score)

Configured in `backend/sensors/fusion.py`:

```python
DEFAULT_WEIGHTS = {
    "ProsodicContinuitySensor": 0.10,
    # ... other sensors
}
```

Can be overridden in `backend/config/settings.yaml`.

## Interpretation

### Break Rates

- **0.0 - 1.0 breaks/sec**: Very smooth, consistent speech
- **1.0 - 2.0 breaks/sec**: Normal human speech variation
- **2.0 - 3.0 breaks/sec**: High natural variation or emphatic speech
- **3.0+ breaks/sec**: Suspicious, possible splicing or artifacts

### Dominant Factors

The sensor identifies which prosodic feature contributes most breaks:

- **Pitch-dominated**: Unnatural pitch jumps (TTS, pitch-shifted)
- **Energy-dominated**: Splicing artifacts, amplitude glitches
- **Timbre-dominated**: Voice morphing, spectral inconsistencies

## Testing

Run tests:

```bash
cd backend
python -m pytest tests/test_prosodic_continuity.py -v
```

Test coverage:
- ✅ Initialization
- ✅ Smooth speech (passes)
- ✅ Spliced speech (fails)
- ✅ No speech (returns None)
- ✅ Ultra-short input (returns None)
- ✅ Invalid input (returns None)
- ✅ White noise
- ✅ Pure tone
- ✅ Natural variation
- ✅ Result serialization
- ✅ Speech with pauses
- ✅ Extreme splicing

## Performance Characteristics

- **Speed**: Fast (numpy/scipy only, no ML inference)
- **Memory**: Low (processes frames sequentially)
- **Accuracy**: Depends on calibration quality
- **False Positives**: Reduced by calibrating with organic samples
- **False Negatives**: May miss very sophisticated TTS with smooth prosody

## Common Issues & Solutions

### High False Positive Rate

**Problem**: Natural speech flagged as synthetic

**Solutions**:
1. Calibrate with more diverse organic samples
2. Increase `max_breaks_per_second` threshold
3. Increase `risk_threshold`
4. Check z-score thresholds (try 3.5 instead of 3.0)

### Low Detection Rate

**Problem**: Synthetic speech not detected

**Solutions**:
1. Verify synthetic samples actually have prosodic discontinuities
2. Decrease `max_breaks_per_second` threshold
3. Decrease `risk_threshold`
4. Check if synthetic speech is high-quality (smooth prosody)

### Too Many "passed=None" Results

**Problem**: Many samples abstain from verdict

**Solutions**:
1. Decrease `min_speech_duration` (but not below 0.3s)
2. Check VAD settings (may be too strict)
3. Ensure audio quality is adequate

## Related Sensors

Works well in combination with:
- **FormantTrajectorySensor**: Detects impossible formant velocities
- **TwoMouthSensor**: Detects anatomical conflicts
- **DigitalSilenceSensor**: Detects splicing artifacts
- **PitchVelocitySensor**: Detects impossible pitch changes

## References

### Prosodic Analysis
- Pitch contour continuity in natural speech
- Energy envelope smoothness
- Spectral continuity and timbre consistency

### Signal Processing
- Short-Time Fourier Transform (STFT) for spectral analysis
- Autocorrelation for pitch estimation
- Z-score normalization for outlier detection

## License

Part of Sonotheia Enhanced, subject to repository license.

## Contributing

To improve this sensor:
1. Add more sophisticated prosodic features
2. Improve F0 estimation robustness
3. Add speaker-adaptive thresholds
4. Implement temporal context modeling

See main repository for contribution guidelines.
