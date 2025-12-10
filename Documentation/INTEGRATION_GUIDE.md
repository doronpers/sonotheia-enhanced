# Sonotheia Integration Guide

This guide details how to integrate the **Sonotheia Deepfake Detection Engine** into 3rd-party platforms and applications.

## Integration Methods

There are two primary ways to consume the detection engine:

1.  **REST API**: For external web services, mobile apps, or microservices (HTTP/JSON).
2.  **Python SDK**: For direct embedding into Python data pipelines or scripts.

---

## 1. REST API Integration

The API is built on **FastAPI** and runs by default on port `8000`.

### Base URL
```
http://localhost:8000/api
```

### Authentication
Include your API Key in the header if configured (optional in dev):
```http
X-API-Key: your_secret_key
```

### Endpoint: Full Detection
Run the complete 6-stage pipeline (including Neural & Physics analysis).

**Request:** `POST /detect`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (Binary audio file: .wav, .mp3, .flac)

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/detect" \
     -H "X-API-Key: secret" \
     -F "file=@/path/to/suspect_audio.wav"
```

**Response (JSON):**
```json
{
  "success": true,
  "detection_score": 0.95,
  "is_spoof": true,
  "confidence": 0.98,
  "decision": "FAKE",
  "explanation": {
    "top_factors": ["RawNet3 High Confidence", "Impossible Breath Pattern"]
  }
}
```

### Endpoint: Quick Scan
Run a lightweight analysis (Stages 1-3 only). < 100ms latency.

**Request:** `POST /detect/quick`
- **Body**: `file` (Binary audio)

### Endpoint: Async Detection (Job Queue)
For batch processing large files without blocking.

1. **Start Job:** `POST /detect/async` -> Returns `{"job_id": "123"}`
2. **Check Status:** `GET /detect/123/status` -> Returns `{"status": "pending|completed"}`
3. **Get Result:** `GET /detect/123/results` -> Returns full JSON report.

---

## 2. Python SDK Integration

If your application is written in Python and running in the same environment, you can import the pipeline directly to zero-latency overhead.

### Installation
Ensure `sonotheia-enhanced` is in your `PYTHONPATH`.

### Basic Usage
```python
from backend.detection import get_pipeline
from backend.sensors.utils import load_and_preprocess_audio
import io

# 1. Initialize Pipeline (Lazy Loading)
pipeline = get_pipeline() 

# 2. Load Audio (supports bytes, path, or BytesIO)
# Returns: audio_array (np.ndarray), sample_rate (int)
with open("test_audio.wav", "rb") as f:
    audio_io = io.BytesIO(f.read())
    audio_array, sr = load_and_preprocess_audio(audio_io)

# 3. specific detection
result = pipeline.detect(audio_array)

# 4. Process Result
if result['success']:
    print(f"Score: {result['detection_score']}")
    print(f"Verdict: {result['decision']}")
else:
    print(f"Error: {result['error']}")
```

### Advanced Configuration
You can customize the pipeline behavior by modifying `backend/config/detection.yaml` or setting environment variables.

- `DEMO_MODE=false`: Ensure real analysis is running.
- `HF_LOCAL_FALLBACK=true`: Enable offline AI models.
