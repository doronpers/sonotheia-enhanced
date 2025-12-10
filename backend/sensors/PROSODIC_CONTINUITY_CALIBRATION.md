# ProsodicContinuitySensor Calibration Guide

## Overview

The ProsodicContinuitySensor detects abrupt prosodic changes in speech that indicate synthetic or spliced audio. To optimize its performance, you can calibrate it using your own organic (authentic) speech samples.

## What Gets Calibrated

The sensor analyzes:
- **F0 (Pitch)**: Fundamental frequency changes over time
- **Energy**: RMS amplitude variations
- **Spectral Centroid**: Timbre/brightness changes

It counts "prosodic breaks" where frame-to-frame changes exceed statistical thresholds (z-scores), then computes a risk score based on break frequency.

## Running Calibration

### Basic Usage

```bash
cd backend/sensors
python calibrate_prosodic.py --organic-dir /path/to/organic/samples
```

### With Output Configuration

```bash
python calibrate_prosodic.py \
    --organic-dir /path/to/organic/samples \
    --output recommended_config.yaml
```

### JSON Output for Further Analysis

```bash
python calibrate_prosodic.py \
    --organic-dir /path/to/organic/samples \
    --json > calibration_stats.json
```

## Input Requirements

### Organic Sample Directory Structure

```
organic_samples/
├── speaker1/
│   ├── sample1.wav
│   ├── sample2.wav
│   └── sample3.wav
├── speaker2/
│   ├── recording1.wav
│   └── recording2.wav
└── ...
```

The script recursively searches for audio files (`.wav`, `.flac`, `.mp3`, `.ogg`).

### Sample Requirements

- **Format**: WAV (preferred), FLAC, MP3, or OGG
- **Duration**: At least 1-2 seconds of speech per file
- **Quality**: Clean recordings without excessive noise
- **Quantity**: Minimum 20-30 samples recommended, more is better
- **Diversity**: Include various:
  - Speakers (different ages, genders, accents)
  - Speaking styles (conversational, formal, emotional)
  - Recording conditions (studio, phone, video call)

## Understanding the Output

### Statistics Reported

```
Breaks per second:
  Mean:   1.23      # Average break rate across all samples
  Median: 1.15      # Middle value (robust to outliers)
  Std:    0.45      # Variability in break rates
  P90:    1.85      # 90th percentile
  P95:    2.10      # 95th percentile (typical max for organic)
  P99:    2.45      # 99th percentile (rare but organic)
  Max:    2.80      # Absolute maximum observed

Break types (fraction of total):
  Pitch:    35%     # Percentage from F0 changes
  Energy:   45%     # Percentage from amplitude changes
  Centroid: 20%     # Percentage from timbre changes
```

### Recommended Thresholds

The script recommends:

```yaml
prosodic_continuity:
  max_breaks_per_second: 2.94  # P99 + 20% margin
  risk_threshold: 0.7          # Moderate sensitivity
  f0_zscore_threshold: 3.0     # Standard outlier detection
  energy_zscore_threshold: 3.0
  centroid_zscore_threshold: 3.0
  min_speech_duration: 0.5
```

## Applying Calibrated Settings

### Option 1: Update settings.yaml

Copy the recommended thresholds to `backend/config/settings.yaml`:

```yaml
sensors:
  prosodic_continuity:
    max_breaks_per_second: 2.94  # From calibration
    risk_threshold: 0.7
    f0_zscore_threshold: 3.0
    energy_zscore_threshold: 3.0
    centroid_zscore_threshold: 3.0
    min_speech_duration: 0.5
```

### Option 2: Use Generated Config File

```bash
# Generate config
python calibrate_prosodic.py \
    --organic-dir /path/to/samples \
    --output calibrated_config.yaml

# Merge into settings.yaml manually or programmatically
```

### Option 3: Override at Runtime

```python
from backend.sensors.prosodic_continuity import ProsodicContinuitySensor

sensor = ProsodicContinuitySensor()
sensor.max_breaks_per_second = 2.94  # Custom value
sensor.risk_threshold = 0.7
```

## Interpretation Guide

### What Break Rates Mean

- **0.0 - 1.0 breaks/sec**: Very smooth, typical of pure tones or highly controlled speech
- **1.0 - 2.0 breaks/sec**: Normal human speech with natural prosodic variation
- **2.0 - 3.0 breaks/sec**: High natural variation or emotional/emphatic speech
- **3.0+ breaks/sec**: Suspicious, possible splicing or synthetic artifacts

### Dominant Factors

The sensor reports which factors contribute most to breaks:

- **Pitch-dominated**: Unnatural pitch jumps (common in pitch-shifted TTS)
- **Energy-dominated**: Splicing artifacts, amplitude glitches
- **Timbre-dominated**: Voice morphing, spectral inconsistencies

## Best Practices

### For Development/Testing

Use **liberal thresholds** (higher `max_breaks_per_second`) to reduce false positives:

```yaml
max_breaks_per_second: 3.5  # P99 + 40% margin
risk_threshold: 0.75
```

### For Production

Use **conservative thresholds** based on your FPR requirements:

```yaml
max_breaks_per_second: 2.5  # P95
risk_threshold: 0.6  # Stricter
```

### Continuous Calibration

Recalibrate periodically as you collect more organic samples:
1. Add new organic samples to your collection
2. Re-run calibration
3. Compare new thresholds with old
4. Update if significant drift detected

## Troubleshooting

### "No samples could be analyzed successfully"

- Check audio file formats (WAV is most reliable)
- Verify files contain actual speech (not silence or noise)
- Ensure sample rate is reasonable (8kHz-48kHz)

### "Expected more breaks but got few"

- Organic samples may be too clean/studio-quality
- Try including more varied recording conditions
- Check if samples are actual human speech (not synthesized)

### Thresholds seem too high/low

- Compare against known synthetic samples
- Adjust `risk_threshold` independently of `max_breaks_per_second`
- Consider your use case (high security vs. user convenience)

## Example Workflow

```bash
# 1. Collect organic samples
mkdir -p organic_samples/collection1
# ... add audio files ...

# 2. Run calibration
python calibrate_prosodic.py \
    --organic-dir organic_samples/collection1 \
    --output calibration_results.yaml \
    --json > calibration_stats.json

# 3. Review statistics
cat calibration_stats.json | jq '.statistics.breaks_per_second'

# 4. Test on synthetic samples
python test_on_synthetic.py --config calibration_results.yaml

# 5. Update production config
# Manually merge calibration_results.yaml into settings.yaml
```

## Advanced: Using Statistics for Research

The JSON output can be used for:
- Comparing organic vs. synthetic distributions
- Training ML models on prosodic features
- Academic research on prosodic characteristics
- Building speaker-specific or accent-specific thresholds

Example analysis:

```python
import json
import numpy as np
import matplotlib.pyplot as plt

# Load calibration results
with open('calibration_stats.json') as f:
    data = json.load(f)

stats = data['statistics']['breaks_per_second']

# Visualize distribution
print(f"Mean: {stats['mean']:.2f}")
print(f"StdDev: {stats['std']:.2f}")
print(f"Range: {stats['min']:.2f} - {stats['max']:.2f}")

# Compare with synthetic samples (your implementation)
```

## Contact & Contributions

For questions or improvements to the calibration process, please open an issue or submit a PR.
