---
title: Implementation Summary
tags: [architecture, implementation, design]
---

# Sonotheia Implementation Summary

Architectural overview of how Sonotheia components work together.

📖 **For design history and comparisons, see [IMPLEMENTATION_COMPARISON.md](IMPLEMENTATION_COMPARISON.md).**

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│   Sensors   │
│  (React)    │     │  (FastAPI)   │     │  (Physics)  │
│   Nginx     │     │   Port 8000  │     │  Registry   │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ SAR/LLM Gen  │
                    │  (Compliance)│
                    └──────────────┘
```

## Component Communication

### Frontend → Backend

1. **User uploads audio** via React component (`frontend/src/components/Demo.jsx`)
2. **FormData sent** to `/api/v2/detect/quick` endpoint
3. **Nginx proxies** API requests to backend (production)
4. **Backend processes** audio through sensor pipeline
5. **Response returned** with verdict and evidence

### Backend → Sensors

1. **Audio decoded** once using `soundfile` (mono conversion, float32 normalization)
2. **Sensor Registry** (`backend/sensors/registry.py`) orchestrates analysis
3. **Each sensor** (`backend/sensors/*.py`) analyzes audio independently
4. **Results aggregated** into unified verdict
5. **Evidence packaged** for response

### Backend → SAR/LLM

1. **Detection triggers** SAR generation (if enabled)
2. **SAR Generator** (`backend/sar/generator.py`) creates compliance narrative
3. **Optional LLM** (`backend/sar/llm_generator.py`) enhances narrative
4. **Output stored** or returned for compliance workflows

## Sensor Framework

### Architecture

**Base Classes:**
- `BaseSensor` (`backend/sensors/base.py`): Abstract sensor interface
- `SensorResult` (`backend/sensors/base.py`): Standardized result format
- `SensorRegistry` (`backend/sensors/registry.py`): Centralized sensor management

**Sensor Pattern:**
```python
class MySensor(BaseSensor):
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        # Analysis logic
        return SensorResult(
            sensor_name="My Sensor",
            passed=True,
            value=0.95,
            threshold=0.8,
            reason="Explanation",
            detail="Details"
        )
The system uses a modular sensor architecture inheriting from `BaseSensor`.

**Active Sensors:**
1.  **GlottalInertiaSensor**: Checks for impossible amplitude rise velocities (Phase 1 Patent-Safe).
2.  **GlobalFormantSensor**: Checks for robotic spectral envelope statistics (Phase 1 Patent-Safe).
3.  **PhaseCoherenceSensor**: Checks for phase entropy and derivative anomalies (Phase 1 Patent-Safe).
4.  **DigitalSilenceSensor**: Checks for non-biological silence signatures.
5.  **CoarticulationSensor**: Checks for natural phoneme transitions.
6.  **BreathSensor**: Checks for "Infinite Lung Capacity".
7.  **DynamicRangeSensor**: Checks crest factor.
8.  **BandwidthSensor**: Checks frequency cutoff.
9.  **HFDeepfakeSensor**: Optional ML-based detection (Wav2Vec2).

**Removed Components:**
- `VocalTractSensor`: Removed due to patent infringement concerns (LPC-based).

## SAR/LLM Generation

### SAR Generation

**Template-based** (`backend/sar/generator.py`):
- Uses Jinja2 templates (`backend/sar/templates/`)
- Generates compliance-ready narratives
- Includes evidence packaging and audit trails

**LLM Enhancement** (`backend/sar/llm_generator.py`):
- Optional AI-powered narrative generation
- Supports Vercel AI Gateway / OpenAI
- Falls back to template if API key missing
- Includes PII redaction

**Code Location:** `backend/sar/`

## Frontend Architecture

### React Components

- **Demo.jsx**: Main audio upload and results display
- **DetectorChat.jsx**: Explanation interface
- **Other components**: About, Contact, Team, etc.

### Build & Serve

- **Build**: Vite compiles React to static assets
- **Serve**: Nginx serves static files in production
- **Proxy**: Nginx proxies `/api/*` to backend

**Code Location:** `frontend/`

## Performance-Optimized Sensor Pipeline

*(Milestone 1: Profiling & Baselines - Completed)*
*(Milestone 2: Optimization - In Progress)*

**Planned Optimizations:**
- Vectorized NumPy operations
- Single audio decode shared across sensors
- Cached FFT results
- Streaming analysis for large files

## Data Flow

1. **Audio Upload** → FastAPI receives multipart/form-data
2. **Validation** → File size, format, sample rate checks
3. **Decode** → `soundfile` reads audio to NumPy array
4. **Preprocess** → Mono conversion, float32 normalization
5. **Sensor Analysis** → Registry executes all sensors
6. **Aggregation** → Verdict determined from sensor results
7. **Response** → JSON with verdict, evidence, metadata

## Configuration

**Settings:** `backend/config/settings.yaml`
- Authentication policies
- Risk assessment thresholds
- SAR generation triggers
- API limits

**Environment Variables:**
- `PORT`: Backend port
- `BACKEND_URL`: Frontend proxy target
- `LLM_API_KEY`: Optional LLM access

## Related Documentation

- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - API integration details
- [ROADMAP.md](ROADMAP.md) - Future improvements and optimizations
- [IMPLEMENTATION_COMPARISON.md](IMPLEMENTATION_COMPARISON.md) - Design history

---

**Last Updated:** 2025-01-XX  
**Version:** 9.0 (Bandwidth Aware)

