---
title: Integration Guide
tags: [integration, api, developers]
---

# Sonotheia Integration Guide

Technical guide for integrating Sonotheia into your application.

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Detection Endpoint](#detection-endpoint)
- [Evidence Structure](#evidence-structure)
- [Sensor Semantics](#sensor-semantics)
- [Code References](#code-references)
- [Integration Patterns](#integration-patterns)

---

## API Overview

Sonotheia provides a RESTful API for voice fraud detection.

**Base URL:** `https://api.sonotheia.ai` (production) or `http://localhost:8000` (development)

**API Version:** v2

**Content-Type:** `multipart/form-data` for file uploads, `application/json` for other endpoints

---

## Authentication

Currently, the API is open (no authentication required). For production deployments:

- API key authentication (planned)
- OAuth 2.0 support (planned)
- Rate limiting per IP (planned)

📖 **See [SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md)** for security considerations.

---

## Detection Endpoint

### POST /api/v2/detect/quick

Analyze an audio file for authenticity.

**Request:**

```http
POST /api/v2/detect/quick
Content-Type: multipart/form-data

file: <audio_file>
```

**cURL Example:**
```bash
curl -X POST https://api.sonotheia.ai/api/v2/detect/quick \
  -F "file=@audio.wav"
```

**Python Example:**
```python
import requests

url = "https://api.sonotheia.ai/api/v2/detect/quick"

with open("audio.wav", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    result = response.json()
    
    print(f"Verdict: {result['verdict']}")
    print(f"Confidence: {result.get('detail', 'N/A')}")
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('file', audioFile);

const response = await fetch('https://api.sonotheia.ai/api/v2/detect/quick', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Verdict:', result.verdict);
```

**Response:**

```json
{
  "verdict": "REAL | SYNTHETIC | UNKNOWN",
  "detail": "Human-readable summary",
  "processing_time_seconds": 0.45,
  "model_version": "sonotheia_deterministic_v9.0_BANDWIDTH_AWARE",
  "evidence": {
    "breath": { ... },
    "dynamic_range": { ... },
    "bandwidth": { ... },
    "phase_coherence": { ... },
    "vocal_tract": { ... },
    "coarticulation": { ... }
  }
}
```

**Verdict Values:**
- `REAL`: Audio appears to be authentic human speech
- `SYNTHETIC`: Audio shows characteristics of AI-generated speech
- `UNKNOWN`: Insufficient signal quality or ambiguous results

---

## Evidence Structure

The `evidence` object contains results from each sensor:

```json
{
  "sensor_name": "Breath Sensor (Max Phonation)",
  "passed": true,
  "value": 8.5,
  "threshold": 14.0,
  "reason": "Max phonation within normal range",
  "detail": "Maximum continuous phonation: 8.5s",
  "metadata": {}
}
```

**Fields:**
- `sensor_name`: Human-readable sensor name
- `passed`: `true` if sensor indicates real speech, `false` if synthetic, `null` if inconclusive
- `value`: Measured value (e.g., phonation duration in seconds)
- `threshold`: Threshold value for this sensor
- `reason`: Brief explanation of the result
- `detail`: Additional details about the measurement
- `metadata`: Optional sensor-specific metadata

---

## Sensor Semantics

### Breath Sensor

**Purpose:** Detects biologically impossible phonation patterns

**Key Metrics:**
- `value`: Maximum continuous phonation duration (seconds)
- `threshold`: 14.0 seconds (human limit)

**Interpretation:**
- `passed: true`: Phonation duration within human limits
- `passed: false`: Phonation exceeds human respiratory capacity (indicates synthetic)

**Code Reference:** `backend/sensors/breath.py`

### Dynamic Range Sensor

**Purpose:** Detects compression artifacts from audio processing

**Key Metrics:**
- `value`: Crest factor (peak/RMS ratio)
- `threshold`: 12.0

**Interpretation:**
- `passed: true`: Natural dynamic range (high crest factor)
- `passed: false`: Compressed/processed audio (low crest factor)

**Code Reference:** `backend/sensors/dynamic_range.py`

### Bandwidth Sensor

**Purpose:** Analyzes frequency spectrum to detect narrowband/telephony audio

**Key Metrics:**
- `value`: Spectral rolloff frequency (Hz)
- `threshold`: 4000 Hz
- `type`: "fullband" or "narrowband"

**Interpretation:**
- `passed: true`: Fullband audio (natural speech)
- `passed: false`: Narrowband audio (telephony or processed)

**Code Reference:** `backend/sensors/bandwidth.py`

### Phase Coherence Sensor

**Purpose:** Detects phase inconsistencies that indicate vocoder artifacts

**Key Metrics:**
- `value`: Phase coherence score (0.0 - 1.0)
- `threshold`: 0.7

**Interpretation:**
- `passed: true`: Natural phase relationships
- `passed: false`: Phase inconsistencies (synthetic artifacts)

**Code Reference:** `backend/sensors/phase_coherence.py`

### Vocal Tract Sensor

**Purpose:** Analyzes formant frequencies to detect unrealistic vocal tract physics

**Key Metrics:**
- `value`: Formant consistency score (0.0 - 1.0)
- `threshold`: 0.8

**Interpretation:**
- `passed: true`: Realistic formant structure
- `passed: false`: Unrealistic formant spacing (synthetic)

**Code Reference:** `backend/sensors/vocal_tract.py`

### Coarticulation Sensor

**Purpose:** Detects unnatural phoneme transitions

**Key Metrics:**
- `value`: Coarticulation score (0.0 - 1.0)
- `threshold`: 0.7

**Interpretation:**
- `passed: true`: Natural phoneme blending
- `passed: false`: Rigid transitions (synthetic)

**Code Reference:** `backend/sensors/coarticulation.py`

---

## Code References

### Main API Implementation

**File:** `backend/main.py`

**Key Functions:**
- `quick_detect()`: Main detection endpoint (line 309)
- `explain_detect()`: Explanation endpoint (line 531)
- `convert_numpy_types()`: NumPy to JSON conversion (line 39)

**Sensor Registry:**
```python
# Lines 197-205
sensor_registry = SensorRegistry()
sensor_registry.register(BreathSensor(), "breath")
sensor_registry.register(DynamicRangeSensor(), "dynamic_range")
sensor_registry.register(BandwidthSensor(), "bandwidth")
sensor_registry.register(PhaseCoherenceSensor(), "phase_coherence")
sensor_registry.register(VocalTractSensor(), "vocal_tract")
sensor_registry.register(CoarticulationSensor(), "coarticulation")
```

### Sensor Framework

**Base Classes:**
- `backend/sensors/base.py`: `BaseSensor`, `SensorResult`
- `backend/sensors/registry.py`: `SensorRegistry`

**Sensor Implementations:**
- `backend/sensors/breath.py`: Breath sensor
- `backend/sensors/dynamic_range.py`: Dynamic range sensor
- `backend/sensors/bandwidth.py`: Bandwidth sensor
- `backend/sensors/phase_coherence.py`: Phase coherence sensor
- `backend/sensors/vocal_tract.py`: Vocal tract sensor
- `backend/sensors/coarticulation.py`: Coarticulation sensor

---

## Integration Patterns

### Pattern 1: Simple Detection

```python
import requests

def detect_audio(audio_file_path):
    url = "https://api.sonotheia.ai/api/v2/detect/quick"
    
    with open(audio_file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
        response.raise_for_status()
        return response.json()

result = detect_audio("audio.wav")
print(f"Verdict: {result['verdict']}")
```

### Pattern 2: With Error Handling

```python
import requests
from requests.exceptions import RequestException

def detect_audio_safe(audio_file_path):
    url = "https://api.sonotheia.ai/api/v2/detect/quick"
    
    try:
        with open(audio_file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files, timeout=60)
            response.raise_for_status()
            return {"success": True, "result": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}"}
    except RequestException as e:
        return {"success": False, "error": str(e)}
```

### Pattern 3: Batch Processing

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def detect_batch(audio_files, max_workers=5):
    url = "https://api.sonotheia.ai/api/v2/detect/quick"
    
    def detect_one(file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(url, files=files, timeout=60)
                response.raise_for_status()
                return {"file": file_path, "result": response.json()}
        except Exception as e:
            return {"file": file_path, "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(detect_one, audio_files))
    
    return results
```

### Pattern 4: With Explanation

```python
def detect_with_explanation(audio_file_path, question):
    # Step 1: Detect
    detect_url = "https://api.sonotheia.ai/api/v2/detect/quick"
    
    with open(audio_file_path, "rb") as f:
        files = {"file": f}
        detect_response = requests.post(detect_url, files=files)
        detect_result = detect_response.json()
    
    # Step 2: Explain
    explain_url = "https://api.sonotheia.ai/api/v2/explain"
    explain_payload = {
        "verdict": detect_result["verdict"],
        "detail": detect_result["detail"],
        "evidence": detect_result["evidence"],
        "question": question
    }
    
    explain_response = requests.post(explain_url, json=explain_payload)
    explain_result = explain_response.json()
    
    return {
        "detection": detect_result,
        "explanation": explain_result
    }
```

---

## Best Practices

1. **File Size**: Keep files under 10MB when possible for faster processing
2. **Format**: Use WAV format for best accuracy
3. **Duration**: 5-60 seconds is optimal
4. **Error Handling**: Always handle HTTP errors and timeouts
5. **Rate Limiting**: Respect rate limits (60 requests/minute default)
6. **Retries**: Implement exponential backoff for retries

---

## Related Documentation

- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Detailed usage examples
- [ENTERPRISE_INTEGRATION.md](ENTERPRISE_INTEGRATION.md) - Enterprise features
- [SECURITY_COMPLIANCE.md](SECURITY_COMPLIANCE.md) - Security considerations
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Architecture overview

---

**Last Updated:** 2025-01-XX  
**API Version:** 9.0 (Bandwidth Aware)

