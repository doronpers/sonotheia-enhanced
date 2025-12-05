---
title: Sonotheia Development Roadmap
tags: [roadmap, milestones, performance, optimization]
---

# Sonotheia Development Roadmap

This document outlines the development milestones for Sonotheia, focusing on performance optimization, accuracy improvements, and scalability enhancements.

**Status Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed

---

## Milestone 0 — Foundation & Compliance (Completed)

**Status:** 🟢 Completed

### Achievements
- ✅ **Patent Compliance**: Refactored `VocalTractSensor` to remove static analysis; enabled `FormantTrajectorySensor` for dynamic velocity detection.
- ✅ **Security**: Patched critical vulnerabilities in backend dependencies (`Jinja2`, `python-multipart`).
- ✅ **Documentation**: Streamlined deployment guides and consolidated documentation.
- ✅ **Architecture**: Established hybrid OOP/FP sensor framework.

---

## Milestone 1 — Profiling & Baseline Metrics

**Status:** 🟢 Completed
**Timeline:** Short-term (1–2 weeks)

### Goals

- Know exactly where latency and inaccuracy come from
- Establish benchmarks per endpoint

### Tasks

#### Baseline Performance Metrics

Add simple timing to:
- Audio loading & normalization
- Each sensor's `analyze(...)` method
- SAR generation
- LLM call (if enabled)

Export to `/metrics` (extend existing metrics endpoints) or log structured JSON for offline analysis.

**Implementation Notes:**
- Extend `MetricsCollector` in `backend/main.py` to track per-sensor timing
- Add timing decorators or context managers around sensor execution
- Log timing data in structured JSON format for analysis

#### Accuracy Benchmarks

Build a small labeled dataset of:
- Human vs synthetic audio with known ground truth
- Different bandwidths, bitrates, noise levels

Add pytest-based "acceptance tests":
- For each sample, expected verdict from each sensor and overall
- Store test fixtures in `backend/tests/fixtures/audio/`

**Test Structure:**
```python
# backend/tests/test_accuracy_benchmarks.py
@pytest.mark.parametrize("audio_file,expected_verdict,expected_sensors", [
    ("human_10s.wav", "REAL", {"breath": True, "dynamic_range": True}),
    ("synthetic_10s.wav", "SYNTHETIC", {"breath": False}),
    # ... more test cases
])
def test_accuracy_benchmark(audio_file, expected_verdict, expected_sensors):
    # Load audio, run detection, assert results
    pass
```

#### Document the Baseline

In this document, record:
- Current median and p95 latency for `/api/v2/detect/quick` for 10s / 30s / 60s audio
- Baseline precision/recall on labeled set

**Baseline Metrics (To Be Measured):**

| Audio Duration | Median Latency | P95 Latency | Target |
|----------------|----------------|-------------|--------|
| 10 seconds     | ~0.5s (est)    | TBD         | < 500ms |
| 30 seconds     | ~1.5s (est)    | TBD         | < 1.5s |
| 60 seconds     | ~3.0s (est)    | TBD         | < 3s |

*Measured Baseline (Local M1 Mac):*
- 0.5s audio: 0.026s
- 1.0s audio: 0.052s
- 2.0s audio: 0.109s
- Scaling appears linear (~0.05s per second of audio).
**Accuracy Metrics (To Be Measured):**

| Metric | Current | Target |
|--------|---------|--------|
| Precision | TBD | > 0.95 |
| Recall | TBD | > 0.90 |
| F1 Score | TBD | > 0.92 |

---

## Milestone 2 — Core Sensor Optimizations

**Status:** 🔴 Not Started
**Timeline:** Short/medium term (2–4 weeks)

### Goals

- Reduce latency per sensor without sacrificing determinism
- Improve signal robustness

### Tasks

#### Vectorization & NumPy Optimization

Review `backend/sensors/*.py`:
- Remove unnecessary Python loops over samples
- Use NumPy vector operations and avoid repeated FFTs when possible
- Ensure all intermediate results are kept as NumPy arrays but convert to native types before JSON using `convert_numpy_types` helper

**Key Files to Optimize:**
- `backend/sensors/breath.py` - Optimize frame-by-frame processing
- `backend/sensors/dynamic_range.py` - Vectorize crest factor calculation
- `backend/sensors/bandwidth.py` - Cache FFT results if used multiple times
- `backend/sensors/phase_coherence.py` - Optimize phase calculations
- `backend/sensors/vocal_tract.py` - Vectorize formant extraction
- `backend/sensors/coarticulation.py` - Optimize phoneme analysis

**Example Optimization Pattern:**
```python
# Before: Python loop
for i in range(len(audio_data)):
    frame = audio_data[i:i+frame_size]
    # process frame

# After: NumPy vectorization
frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_size)
results = np.apply_along_axis(process_frame, 1, frames)
```

#### Audio IO & Preprocessing

Ensure:
- Audio is decoded once (e.g., via `soundfile`) and shared across sensors
- Resampling and normalization happen once upstream of sensors

For large files (up to 800 MB), consider:
- Chunked reading + streaming analysis for sensors that can operate incrementally
- Memory-mapped file access for very large files

**Implementation:**
- Refactor `backend/main.py` to decode audio once before sensor execution
- Create `backend/sensors/utils.py` preprocessing functions
- Add streaming support for sensors that support it (e.g., breath sensor)

#### Sensor-Specific Robustness

For `breath.py`, `dynamic_range.py`, `bandwidth.py`:
- Confirm thresholds are in `backend/config/settings.yaml` (not hard-coded)
- Add tests under `backend/tests/*` that check borderline cases around thresholds
- Add a new accuracy-focused sensor if helpful (e.g., spectral flatness / harmonicity sensor) to better distinguish TTS from real speech

**Configuration Migration:**
```yaml
# backend/config/settings.yaml
sensors:
  breath:
    max_phonation_seconds: 14.0
    silence_threshold_db: -60
    frame_size_seconds: 0.02
  dynamic_range:
    min_crest_factor: 12.0
  bandwidth:
    min_rolloff_hz: 4000.0
```

**New Sensor Candidate:**
- **Spectral Harmonicity Sensor**: Measures harmonic-to-noise ratio to detect TTS artifacts
- Location: `backend/sensors/harmonicity.py`

#### Documentation Updates

In `Documentation/IMPLEMENTATION_SUMMARY.md`, add section "Performance-Optimized Sensor Pipeline".

In `Documentation/USAGE_GUIDE.md`, document:
- Expected latency envelope
- Trade-offs (e.g., max audio length)
- Performance characteristics per sensor

---

## Milestone 3 — Multi-sensor Fusion & Calibration

**Status:** 🔴 Not Started
**Timeline:** Medium term (3–6 weeks)

### Goals

- Improve overall accuracy by combining sensor outputs instead of naive rules
- Calibrate decisions for enterprise use cases

### Tasks

#### Unified Scoring / Fusion Logic

In `backend/main.py` or a new module (`backend/fusion.py`):
- Introduce a function that takes `SensorResult` objects and returns a combined score / confidence
- Keep it deterministic (e.g., weighted rules) initially:
  - Avoid non-deterministic ML unless you add a fixed seed and reproducible data

**Fusion Strategy:**
```python
# backend/fusion.py
def fuse_sensor_results(results: List[SensorResult]) -> Dict[str, Any]:
    """
    Combine sensor results into unified verdict and confidence.
    
    Strategy:
    - Weighted voting based on sensor reliability
    - Confidence based on agreement between sensors
    - Deterministic (no randomness)
    """
    weights = {
        "breath": 0.3,
        "dynamic_range": 0.25,
        "bandwidth": 0.25,
        "phase_coherence": 0.1,
        "vocal_tract": 0.05,
        "coarticulation": 0.05,
    }
    
    # Calculate weighted score
    # Determine confidence from sensor agreement
    # Return verdict and confidence
```

#### Calibration on Labeled Data

Use labeled dataset to:
- Tune thresholds (dynamic range, bandwidth, breath)
- Optimize weights for fusion logic
- Encode chosen thresholds in `settings.yaml` and document in `Documentation/SECURITY_COMPLIANCE.md` as part of "detection policy"

**Calibration Process:**
1. Run detection on labeled dataset
2. Measure precision/recall for each threshold combination
3. Select optimal thresholds that maximize F1 score
4. Update `settings.yaml` with calibrated values
5. Document calibration methodology and results

#### SAR Alignment

Ensure the SAR (and LLM output, if enabled) explains:
- Which sensors drove the decision
- Confidence-style explanations ("High bandwidth with low breathiness indicates synthetic speech")

**Implementation:**
- Update `backend/sar/generator.py` to include sensor-specific explanations
- Enhance `backend/sar/llm_generator.py` prompts to emphasize sensor contributions
- Add sensor attribution to SAR narrative templates

#### Documentation

Add section to `Documentation/ENTERPRISE_INTEGRATION.md`:
- "Detection Confidence & Policy Tuning"

Add section to `Documentation/USAGE_GUIDE.md`:
- API parameters that might influence strictness (if any)
- How to interpret confidence scores

---

## Milestone 4 — Scaling & Throughput

**Status:** 🔴 Not Started
**Timeline:** Medium/long term (4–8 weeks)

### Goals

- Handle more concurrent detection requests reliably
- Maintain or improve latency under load

### Tasks

#### Async & Concurrency

Confirm FastAPI endpoints use:
- Non-blocking IO where applicable
- A sensible worker model (uvicorn/gunicorn) tuned for CPU-bound sensor work
- Offload heavy work to a worker pool (e.g., `concurrent.futures.ProcessPoolExecutor`) if single-process CPU is a bottleneck

**Implementation:**
```python
# backend/main.py
from concurrent.futures import ProcessPoolExecutor
import asyncio

executor = ProcessPoolExecutor(max_workers=4)

@app.post("/api/v2/detect/quick")
async def quick_detect(file: UploadFile = File(...)):
    # Non-blocking file read
    file_content = await file.read()
    
    # Offload CPU-intensive sensor work to process pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        run_sensor_analysis,
        file_content
    )
    
    return result
```

**Worker Configuration:**
- Use `uvicorn` with multiple workers: `uvicorn main:app --workers 4`
- Or `gunicorn` with uvicorn workers: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`

#### Horizontal Scaling

Document:
- How to run multiple backend instances behind nginx
- Any stateful components that might need externalization (e.g., logging, metrics DB)

Ensure `Documentation/DEPLOYMENT.md` covers:
- Auto-scaling guidelines (if used with Render autoscaling or similar)
- Load balancer configuration
- Session affinity requirements (if any)

**Nginx Load Balancer Config:**
```nginx
upstream sonotheia_backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://sonotheia_backend;
    }
}
```

#### Streaming & Partial Results (Optional)

Explore:
- Accepting "chunked" audio or progressive upload
- Returning intermediate sensor results (for long files) if that helps UX

**Implementation Considerations:**
- WebSocket or Server-Sent Events for streaming results
- Chunked upload support in FastAPI
- Progressive sensor execution with partial result aggregation

#### Testing & Monitoring

Add load tests (possibly separate repo or `tests/perf/`):
- Script using `locust` or `pytest + asyncio` to generate load
- Measure latency under various load conditions
- Identify bottlenecks

Update `Documentation/SECURITY_COMPLIANCE.md`:
- Under "Operational Resilience / Rate Limiting" if you add protections
- Document rate limiting strategy and thresholds

**Load Test Example:**
```python
# tests/perf/test_load.py
import asyncio
import aiohttp
import time

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):  # 100 concurrent requests
            task = session.post(
                'http://localhost:8000/api/v2/detect/quick',
                data={'file': open('test_audio.wav', 'rb')}
            )
            tasks.append(task)
        
        start = time.time()
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        print(f"100 requests in {elapsed:.2f}s")
        print(f"Average: {elapsed/100:.3f}s per request")
```

---

## Future Considerations

### Rust Integration
- Consider migrating CPU-intensive sensors to Rust (see `backend/sonotheia_rust/`)
- Use Python bindings via `maturin` or `pyo3`
- Maintain Python API compatibility

### ML Model Integration ✅ IMPLEMENTED
- ✅ HuggingFace wav2vec2-based deepfake detection sensor
- ✅ Speaker embedding extraction for voice verification
- ✅ HuggingFace Inference API for LLM-powered explanations
- ✅ Graceful fallback when HuggingFace unavailable
- See: `Documentation/HUGGINGFACE_INTEGRATION.md`

### Advanced Features
- Real-time streaming analysis
- Batch processing API
- Webhook notifications for SAR generation
- Multi-tenant support with data isolation

---

## Success Criteria

### Milestone 1
- ✅ Performance metrics collected and documented
- ✅ Labeled dataset created with > 50 samples
- ✅ Baseline accuracy benchmarks established

### Milestone 2
- ✅ Sensor latency reduced by > 30%
- ✅ All thresholds moved to `settings.yaml`
- ✅ New accuracy-focused sensor added (if beneficial)

### Milestone 3
- ✅ Fusion logic implemented and tested
- ✅ Calibrated thresholds documented
- ✅ SAR explanations include sensor attribution

### Milestone 4
- ✅ Support for 10+ concurrent requests without degradation
- ✅ Load testing framework in place
- ✅ Horizontal scaling documented

---

## Related Documentation

- `Documentation/USAGE_GUIDE.md` - API usage and examples
- `Documentation/IMPLEMENTATION_SUMMARY.md` - Architecture overview
- `Documentation/DEPLOYMENT.md` - Deployment guidelines
- `Documentation/SECURITY_COMPLIANCE.md` - Security and compliance
- `backend/config/settings.yaml` - Configuration reference

---

**Last Updated:** 2025-12-03
**Maintainer:** Sonotheia Development Team

