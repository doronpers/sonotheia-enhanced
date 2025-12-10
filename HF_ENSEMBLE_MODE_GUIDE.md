# HFEnsembleSensor Mode Selection Guide

## Overview

The `HFEnsembleSensor` has been refactored to intelligently select its operating mode based on available resources. This removes the hard dependency on `HUGGINGFACE_TOKEN` and enables the sensor to operate in different modes depending on the environment.

## Operating Modes

### 1. API Mode
Uses HuggingFace Inference API for deepfake detection.

**Requirements:**
- `HUGGINGFACE_TOKEN` environment variable set

**Behavior:**
- Calls HuggingFace API for model inference
- Rate limiting and retry logic applied
- Can fallback to local mode if API fails (when enabled)

### 2. Local Mode
Uses local transformers models for deepfake detection.

**Requirements:**
- GPU available (detected via `torch.cuda.is_available()`)
- PyTorch and transformers libraries installed

**Behavior:**
- Downloads and caches models locally (first time)
- Runs inference on local GPU/CPU
- No API calls made
- No rate limits

### 3. Disabled Mode
Sensor is disabled and fails open (passes all samples).

**Conditions:**
- No `HUGGINGFACE_TOKEN` set
- No GPU available

**Behavior:**
- Sensor returns passing results for all samples
- Logs warning on initialization
- No models loaded or API calls made

## Automatic Mode Selection

By default (`HF_MODE=auto`), the sensor automatically selects the best mode:

```
┌─────────────────────┬─────────────┬──────────────┐
│                     │ GPU Present │  No GPU      │
├─────────────────────┼─────────────┼──────────────┤
│ Token Present       │ API Mode    │ API Mode     │
│ No Token            │ Local Mode  │ Disabled     │
└─────────────────────┴─────────────┴──────────────┘
```

## Environment Variables

### Required (None!)
The sensor no longer requires any environment variables to initialize. It will gracefully disable if no resources are available.

### Optional

#### `HUGGINGFACE_TOKEN`
- **Type:** String (API token)
- **Default:** Not set
- **Description:** HuggingFace API token for using Inference API

#### `HF_MODE`
- **Type:** String
- **Options:** `auto`, `api`, `local`
- **Default:** `auto`
- **Description:** Force a specific operating mode
  - `auto`: Automatic selection based on resources
  - `api`: Force API mode (requires token)
  - `local`: Force local mode (requires GPU/transformers)

#### `HF_LOCAL_FALLBACK`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable fallback to local mode if API fails

#### `HF_WARMUP_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Warm up models on initialization (API mode only)

#### `HF_ENSEMBLE_MODELS`
- **Type:** Comma-separated string
- **Default:** `MelodyMachine/Deepfake-audio-detection-V2,mo-thecreator/Deepfake-audio-detection`
- **Description:** List of model IDs to use in ensemble

## Usage Examples

### Example 1: Production with API
```bash
export HUGGINGFACE_TOKEN=hf_xxx...
# Sensor will use API mode
```

### Example 2: Local Development with GPU
```bash
# No token needed
# Sensor will automatically detect GPU and use local mode
```

### Example 3: CI/CD without GPU
```bash
# No token, no GPU
# Sensor will be disabled and fail open (pass all samples)
# This is safe for testing environments
```

### Example 4: Force Local Mode
```bash
export HF_MODE=local
# Even if token is set, will use local mode
```

## Benefits

1. **No Hard Dependencies:** System starts without requiring `HUGGINGFACE_TOKEN`
2. **Intelligent Fallback:** Automatically uses best available method
3. **Fail-Safe:** Disables gracefully when no resources available
4. **Flexible:** Can force specific modes for testing/development
5. **Cost-Effective:** Uses local GPU when available, reducing API costs

## Migration from Previous Version

### Before
```python
# Required HUGGINGFACE_TOKEN or sensor would fail/skip
if not os.getenv("HUGGINGFACE_TOKEN"):
    logger.warning("Sensor will be skipped")
```

### After
```python
# No token required, sensor adapts automatically
# Mode selection happens transparently
# - With token → API mode
# - No token + GPU → Local mode  
# - No token + no GPU → Disabled (fail open)
```

### Breaking Changes
**None!** The changes are backward compatible. Existing deployments with `HUGGINGFACE_TOKEN` will continue to work unchanged.

## Monitoring

Check sensor mode at runtime:

```python
sensor = HFEnsembleSensor()
status = sensor.get_model_status()

print(f"Mode: {status['mode']}")           # 'api', 'local', or 'disabled'
print(f"GPU Available: {status['gpu_available']}")
print(f"API Available: {status['api_available']}")
```

## Logging

The sensor logs its mode selection on initialization:

```
INFO: HFEnsembleSensor initialized: mode=local, models=2, gpu=True
INFO: HFEnsembleSensor using local mode: GPU detected, running models locally.
```

Or when disabled:

```
INFO: HFEnsembleSensor initialized: mode=disabled, models=2, gpu=False
WARNING: HFEnsembleSensor disabled: No HUGGINGFACE_TOKEN and no GPU available. Sensor will fail open (pass all samples).
```

## Testing

The sensor can be tested in all modes:

```python
import asyncio
import numpy as np
from backend.sensors.hf_ensemble import HFEnsembleSensor

async def test():
    sensor = HFEnsembleSensor()
    await sensor.initialize()
    
    # Generate test audio
    audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    # Analyze
    result = await sensor.analyze(audio, 16000)
    
    print(f"Mode: {sensor._mode}")
    print(f"Result: {result.passed}")
    print(f"Detail: {result.detail}")

asyncio.run(test())
```

## Troubleshooting

### Issue: Sensor is disabled but I have GPU
**Cause:** PyTorch not installed or not detecting GPU

**Solution:**
```bash
pip install torch
python -c "import torch; print(torch.cuda.is_available())"
```

### Issue: Want to use API but sensor uses local mode
**Cause:** Mode auto-selection based on resources

**Solution:**
```bash
export HF_MODE=api
export HUGGINGFACE_TOKEN=hf_xxx...
```

### Issue: Local mode downloads models every time
**Cause:** HuggingFace cache not persistent

**Solution:**
```bash
# Set cache directory
export HF_HOME=/path/to/persistent/cache
```
