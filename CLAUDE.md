# CLAUDE.md - AI Assistant Guide for Sonotheia Enhanced

> Comprehensive guide for AI assistants working with the Sonotheia Enhanced codebase

**Last Updated**: 2025-12-10
**Project Version**: Showcase-ready with Incode integration
**Repository**: doronpers/sonotheia-enhanced

---

## Quick Orientation

### What is Sonotheia Enhanced?

Sonotheia Enhanced is a **multi-factor voice authentication and suspicious activity reporting (SAR) platform** designed for financial institutions and real estate transactions. It combines:

- **Voice Deepfake Detection**: Physics-based, patent-safe acoustic analysis
- **Multi-Factor Authentication**: Voice, device, and behavioral factor orchestration
- **Risk Assessment**: Transaction-level scoring with explainable AI
- **Automated SAR Generation**: Compliance reporting with narrative generation
- **Real-time Processing**: Celery-based async processing with Redis
- **Interactive Dashboard**: React-based UI with waveform visualization

**Current Status**: Production-ready, integrated with Incode's biometric onboarding platform

### Technology Stack at a Glance

**Backend**: Python 3.11+ • FastAPI • PyTorch • Celery • Redis • Rust (performance sensors)
**Frontend**: React 18 • Material-UI • Plotly.js • Wavesurfer.js
**Infrastructure**: Docker • GitHub Actions • Render.com ready
**Testing**: pytest • httpx • pytest-asyncio

---

## Repository Structure

### Root Layout

```
sonotheia-enhanced/
├── backend/                    # Python/FastAPI backend (28 modules, 206 files, 31K+ lines)
├── frontend/                   # React dashboard with MUI
├── reusable-components/        # Shared library (API patterns, sensors, test utils, UI)
├── react-native-sdk/          # Mobile integration SDK
├── Documentation/             # Comprehensive guides and reports
├── scripts/                   # CI/CD and automation
├── demo/                      # Demo profiles and setup
├── .github/workflows/         # CI/CD pipelines
├── docker-compose.yml         # Multi-service orchestration
├── modules.yaml              # Module configuration
├── start.sh / start.bat      # Quick-start scripts
└── [test/calibration scripts]
```

### Backend Architecture (`/backend/`)

**28 core modules organized by function:**

```
backend/
├── api/                       # FastAPI routes, middleware, validation
│   ├── main.py               # Application entry point (START HERE)
│   ├── middleware.py         # Rate limiting, request tracking, security
│   ├── validation.py         # Input sanitization (SQL, XSS, path traversal)
│   ├── routes/               # Modular route handlers
│   ├── [detection, transcription, library, escalation, audit routers]
│
├── authentication/           # MFA orchestration
│   ├── mfa_orchestrator.py  # Main decision engine (KEY FILE)
│   ├── voice_factor.py      # Voice authentication
│   ├── device_factor.py     # Device trust scoring
│   └── unified_orchestrator.py  # Legacy orchestrator
│
├── detection/               # 6-stage deepfake detection pipeline
│   ├── pipeline.py          # Main orchestrator (START HERE)
│   ├── stages/
│   │   ├── feature_extraction.py    # LFCC, CQCC, spectrogram
│   │   ├── temporal_analysis.py     # Temporal patterns
│   │   ├── artifact_detection.py    # Audio artifacts
│   │   ├── rawnet3_neural.py       # Deep learning (RawNet3)
│   │   ├── physics_analysis.py     # Physics-based sensors
│   │   ├── fusion_engine.py        # Multi-stage fusion
│   │   └── explainability.py       # Explanation generation
│   ├── models/              # RawNet3 implementation
│   └── utils/               # Audio loading, preprocessing
│
├── sensors/                 # Physics-based detection (10+ sensors)
│   ├── base.py             # BaseSensor interface (EXTEND THIS)
│   ├── registry.py         # SensorRegistry (KEY FILE)
│   ├── fusion.py           # Sensor fusion logic
│   ├── formant_trajectory.py    # Velocity analysis (35% weight)
│   ├── phase_coherence.py       # Entropy detection (25%)
│   ├── coarticulation.py        # Motor planning (20%)
│   ├── breath.py                # Phonation duration (15%)
│   ├── glottal_inertia.py       # Amplitude rise velocity (15%)
│   ├── [additional sensors: dynamic_range, global_formants, digital_silence, etc.]
│   └── hf_ensemble.py           # HuggingFace transformers (optional)
│
├── sonotheia_rust/         # High-performance Rust sensors
│   ├── src/sensors/        # VacuumSensor, PhaseSensor, ArticulationSensor
│   ├── src/utils/          # Audio processing, FFT
│   ├── Cargo.toml
│   └── [PyO3 bindings for Python integration]
│
├── sar/                    # Suspicious Activity Report generation
│   ├── generator.py        # SAR narrative builder (KEY FILE)
│   ├── models.py           # Pydantic models
│   ├── pdf_generator.py    # PDF export
│   ├── huggingface_llm.py  # LLM enhancement
│   └── templates/sar_narrative.j2
│
├── config/                 # Configuration management
│   ├── settings.yaml       # Central config (EDIT THIS)
│   └── constants.py        # Shared constants, regex patterns
│
├── [additional modules]
│   ├── risk_engine/        # Transaction risk scoring
│   ├── transcription/      # Whisper integration
│   ├── telephony/          # Codec simulation
│   ├── features/           # Audio feature extraction
│   ├── models/             # ML model implementations
│   ├── evaluation/         # Metrics, benchmarking
│   ├── calibration/        # Sensor calibration
│   ├── data_ingest/        # Audio loading, metadata
│   ├── observability/      # Prometheus metrics
│   ├── rate_limiting/      # API rate limiting
│   ├── tasks/              # Celery task definitions
│   ├── ui/                 # Streamlit MVP interface
│   ├── sdk/                # External integration SDK
│   ├── core/               # Core utilities
│   └── utils/              # General utilities
│
├── tests/                  # Comprehensive test suite (20+ files)
│   ├── test_api.py
│   ├── test_detection/
│   ├── test_patent_compliance.py
│   ├── test_rust_sensors.py
│   └── [unit, integration, compliance tests]
│
├── scripts/                # Development and ops scripts
│   ├── test_pipeline.py
│   ├── run_benchmark.py
│   ├── generate_accuracy_report.py
│   ├── calibrate_library.py
│   └── [data ingestion, training, red team scripts]
│
├── data/                   # Data storage
├── static/                 # Static assets
├── ui/                     # Streamlit UI
├── requirements.txt        # Python dependencies
└── Dockerfile             # Backend container
```

### Frontend Architecture (`/frontend/`)

```
frontend/
├── src/
│   ├── components/
│   │   ├── WaveformDashboard.jsx    # Audio visualization (Plotly)
│   │   ├── FactorCard.jsx           # Authentication factor cards
│   │   ├── RiskScoreBox.jsx         # Risk indicator
│   │   ├── EvidenceModal.jsx        # Detailed evidence modal
│   │   ├── AuthenticationForm.jsx   # MFA form
│   │   ├── SARGenerationForm.jsx    # SAR interface
│   │   ├── SARReportsTab.jsx        # SAR listing
│   │   ├── SARDetailView.jsx        # SAR details
│   │   ├── SARAnalyticsDashboard.jsx
│   │   ├── ForensicViewer.jsx       # Audio forensics
│   │   ├── Laboratory.jsx           # Testing interface
│   │   ├── Dashboard.jsx
│   │   └── widgets/                 # Reusable widgets
│   ├── App.js                       # Main app (START HERE)
│   └── index.js                     # Entry point
├── public/
├── package.json
└── Dockerfile                       # Multi-stage nginx build
```

### Reusable Components (`/reusable-components/`)

Production-ready library for code reuse across projects:

```
reusable-components/
├── api-patterns/          # FastAPI patterns
│   ├── middleware.py      # Metrics, error handling
│   ├── response.py        # Response builders
│   └── validation.py      # File validation
│
├── sensor-framework/      # Plugin architecture
│   ├── base.py           # BaseSensor interface
│   └── registry.py       # SensorRegistry
│
├── test-utils/           # Testing utilities
│   ├── generators.py     # Audio test data
│   ├── boundary.py       # Boundary testing
│   ├── edge_cases.py     # Edge case generation
│   ├── assertions.py     # Custom assertions
│   └── performance.py    # Performance testing
│
├── ui-components/        # React components
│   ├── UploadArea.jsx/tsx
│   ├── LoadingSpinner.tsx
│   ├── VerdictDisplay.tsx
│   ├── ErrorDisplay.tsx
│   └── [hooks: useFileUpload]
│
└── HYBRID_OOP_FP_GUIDE.md  # Architectural patterns
```

---

## Key Files Reference

### Essential Configuration Files

| File | Purpose | When to Edit |
|------|---------|-------------|
| `/backend/config/settings.yaml` | Central config: thresholds, policies, sensor weights | Changing detection behavior, MFA policies |
| `/modules.yaml` | Module enable/disable switches | Toggling features (transcription, SAR, etc.) |
| `/docker-compose.yml` | Multi-service orchestration | Adding services, changing ports |
| `/.env.example` | Environment variable template | API keys, demo mode, log levels |
| `/backend/requirements.txt` | Python dependencies | Adding/updating packages |
| `/frontend/package.json` | Node.js dependencies | Frontend packages |

### Critical Entry Points

| File | Purpose | Start Here When... |
|------|---------|-------------------|
| `/backend/api/main.py` | FastAPI application entry | Understanding API structure |
| `/backend/detection/pipeline.py` | Detection orchestrator | Understanding detection flow |
| `/backend/sensors/registry.py` | Sensor plugin system | Adding/modifying sensors |
| `/backend/authentication/mfa_orchestrator.py` | MFA decision engine | Understanding auth logic |
| `/backend/sar/generator.py` | SAR narrative builder | SAR generation logic |
| `/frontend/src/App.js` | React application entry | Understanding UI structure |

### Important Documentation

| File | Contents |
|------|----------|
| `/README.md` | Project overview, quick start, API endpoints |
| `/Documentation/ARCHITECTURE_REFERENCE.md` | Complete system architecture |
| `/Documentation/PATENT_COMPLIANCE.md` | Patent safety analysis |
| `/Documentation/Guides/INCODE_INTEGRATION_GUIDE.md` | Incode integration |
| `/backend/MVP_README.md` | MVP usage and API docs |
| `/reusable-components/HYBRID_OOP_FP_GUIDE.md` | Architectural patterns |

---

## Development Workflows

### Initial Setup

**Using Docker (Recommended):**
```bash
./start.sh              # Linux/Mac
start.bat               # Windows
# OR
docker compose up --build
```

**Manual Setup:**
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install --legacy-peer-deps
npm start
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery): http://localhost:5555

### Common Development Tasks

#### 1. Adding a New Sensor

```python
# Step 1: Create sensor class in /backend/sensors/
from backend.sensors.base import BaseSensor, SensorResult

class MySensor(BaseSensor):
    def __init__(self):
        super().__init__(
            name="my_sensor",
            description="Description of what this detects"
        )

    def analyze(self, audio_data: np.ndarray, sample_rate: int,
                context: dict) -> SensorResult:
        # Your analysis logic
        value = compute_metric(audio_data)
        threshold = self.config.get('threshold', 0.5)

        return SensorResult(
            sensor_name=self.name,
            passed=value < threshold,
            value=value,
            threshold=threshold,
            detail=f"Metric value: {value:.3f}"
        )

# Step 2: Register in /backend/sensors/registry.py
from backend.sensors.my_sensor import MySensor

class SensorRegistry:
    def __init__(self):
        # ... existing code
        self.register(MySensor())

# Step 3: Add config in /backend/config/settings.yaml
sensors:
  my_sensor:
    threshold: 0.5
    weight: 0.15  # Contribution to final score

# Step 4: Write tests in /backend/tests/test_detection/
def test_my_sensor():
    sensor = MySensor()
    test_audio = generate_test_audio()
    result = sensor.analyze(test_audio, 16000, {})
    assert result.sensor_name == "my_sensor"
    assert 0.0 <= result.value <= 1.0
```

#### 2. Adding an API Endpoint

```python
# Step 1: Create route in /backend/api/routes/ or add to existing router
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

class MyRequest(BaseModel):
    param1: str
    param2: int

class MyResponse(BaseModel):
    result: str
    status: str

@router.post("/process", response_model=MyResponse)
async def process_request(request: MyRequest):
    """
    Process a request with my feature.

    - **param1**: Description of param1
    - **param2**: Description of param2
    """
    # Your logic here
    result = do_something(request.param1, request.param2)

    return MyResponse(result=result, status="success")

# Step 2: Include router in /backend/api/main.py
from backend.api.routes.my_feature import router as my_feature_router

app.include_router(my_feature_router)

# Step 3: Add rate limiting if needed (in middleware.py)
@limiter.limit("20/minute")
async def process_request(request: MyRequest):
    # ...

# Step 4: Write integration test
async def test_my_endpoint(client):
    response = await client.post(
        "/api/my-feature/process",
        json={"param1": "test", "param2": 42}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

#### 3. Modifying Detection Logic

```bash
# Step 1: Locate the relevant stage
cd backend/detection/stages/

# Step 2: Edit the stage file (e.g., physics_analysis.py)
# Make your changes

# Step 3: Test the pipeline
cd ../..
python scripts/test_pipeline.py

# Step 4: Run benchmarks to verify performance
python scripts/run_benchmark.py --config scripts/benchmark_config.yaml

# Step 5: If thresholds changed, recalibrate
python scripts/calibrate_library.py --profile default

# Step 6: Update tests
pytest tests/test_detection/ -v
```

#### 4. Frontend Component Changes

```jsx
// Step 1: Locate component in /frontend/src/components/
// Step 2: Make changes following Material-UI patterns
import { Box, Card, Typography } from '@mui/material';

function MyComponent({ data }) {
  return (
    <Card>
      <Box p={2}>
        <Typography variant="h6">{data.title}</Typography>
        <Typography>{data.description}</Typography>
      </Box>
    </Card>
  );
}

// Step 3: Test locally
// npm start (should already be running)

// Step 4: Update API calls if needed
import axios from 'axios';

const fetchData = async () => {
  const response = await axios.get('http://localhost:8000/api/endpoint');
  return response.data;
};
```

### Testing Workflows

#### Backend Testing

```bash
# Run all tests
cd backend
pytest

# Run specific test file
pytest tests/test_api.py

# Run specific test function
pytest tests/test_api.py::test_authentication

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=backend --cov-report=html

# Run only fast tests (exclude slow benchmarks)
pytest -m "not slow"

# Run integration tests only
pytest tests/test_api.py tests/test_detection/
```

#### Frontend Testing

```bash
cd frontend
npm test                    # Interactive watch mode
npm test -- --coverage     # With coverage report
```

#### Manual API Testing

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Authentication endpoint
curl -X POST http://localhost:8000/api/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "transaction_id": "test123",
      "customer_id": "cust456",
      "amount_usd": 1000
    },
    "factors": {
      "voice": {"audio_data": "base64_encoded_audio"},
      "device": {"device_id": "device123"}
    }
  }'

# Interactive API docs
# Open browser: http://localhost:8000/docs
```

### Code Quality Checks

```bash
# Python formatting (auto-fix)
cd backend
black .

# Python linting
flake8 .

# Check without fixing
black --check .

# Frontend linting
cd frontend
npm run lint
```

### Git Workflow

**Branch Strategy:**
- `main`: Production-ready code (protected)
- `develop`: Active development
- `claude/*`: AI-assisted feature branches

**Making Changes:**
```bash
# Always work on the designated branch
git status  # Verify you're on the right branch

# Make your changes, then:
git add .
git commit -m "feat: Add new sensor for articulation analysis

- Implement ArticulationSensor extending BaseSensor
- Add configuration to settings.yaml
- Include comprehensive tests
- Update documentation"

# Push to remote (with retries for network issues)
git push -u origin claude/your-branch-name
```

**Commit Message Conventions:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

---

## Key Conventions

### Code Style

#### Python
- **Formatting**: Black (line length 88)
- **Linting**: Flake8
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Type hints**: Encouraged (helps with IDE support)
- **Docstrings**: Google-style for public APIs

```python
def analyze_audio(audio_data: np.ndarray, sample_rate: int) -> dict:
    """
    Analyze audio data for deepfake detection.

    Args:
        audio_data: Raw audio samples as numpy array
        sample_rate: Sample rate in Hz (typically 16000)

    Returns:
        Dictionary containing analysis results with keys:
        - verdict: "REAL" or "FAKE"
        - confidence: Float between 0.0 and 1.0
        - evidence: Dict of supporting evidence

    Raises:
        ValueError: If sample_rate is not supported
    """
    # Implementation
```

#### JavaScript/React
- **Naming**: camelCase for functions/variables, PascalCase for components
- **Components**: Functional components with hooks
- **File naming**: PascalCase for component files
- **Props**: Destructure in function signature

```jsx
// Good
function FactorCard({ title, score, evidence, onExpand }) {
  const [expanded, setExpanded] = useState(false);
  // ...
}

// Component files: FactorCard.jsx
```

### Configuration Patterns

#### Using settings.yaml

```yaml
# Organized by module
authentication_policy:
  minimum_factors: 2
  risk_thresholds:
    low: 30
    medium: 60
    high: 80

# Sensor thresholds (calibrated values)
sensors:
  glottal_inertia:
    min_rise_time_ms: 10.0
    threshold: 14.0
  formant_trajectory:
    consistency_threshold: 0.7068

# Feature flags
demo_mode: true
```

#### Environment Variables

```bash
# .env file (create from .env.example)
DEMO_MODE=true
LOG_LEVEL=INFO
ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
MODULE_TRANSCRIPTION=1  # Override modules.yaml
```

### Module System (modules.yaml)

Enable/disable entire modules without code changes:

```yaml
audio: true              # Audio processing
analysis: true           # Audio analysis
detection: true          # Deepfake detection
calibration: true        # Sensor calibration
transcription: false     # Speech-to-text (requires API key)
risk_engine: true        # Risk scoring
sar: true               # SAR generation
rate_limiting: true     # API rate limiting
celery: true            # Async processing
observability: true     # Prometheus metrics
tenants: false          # Multi-tenancy
mlflow: false           # ML experiment tracking
```

**Override with environment variables:**
```bash
MODULE_TRANSCRIPTION=1 python api/main.py
```

### API Response Patterns

**Consistent response structure:**

```python
# Success response
{
  "status": "success",
  "data": {
    "verdict": "REAL",
    "confidence": 0.95,
    "evidence": {...}
  },
  "metadata": {
    "request_id": "req_123",
    "processing_time": 1.234,
    "model_version": "v9.0"
  }
}

# Error response
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid audio format",
    "details": {...}
  },
  "metadata": {
    "request_id": "req_123"
  }
}
```

### Error Handling

```python
# Backend: Use appropriate HTTP status codes
from fastapi import HTTPException

if not valid:
    raise HTTPException(
        status_code=400,
        detail="Invalid audio format. Expected WAV, got MP3"
    )

# Frontend: User-friendly error messages
try {
  const response = await axios.post('/api/authenticate', data);
} catch (error) {
  const message = error.response?.data?.error?.message
    || 'An unexpected error occurred';
  setError(message);
}
```

---

## Architecture Patterns

### Sensor Plugin Architecture

All sensors extend `BaseSensor` and register with `SensorRegistry`:

```python
# base.py
class BaseSensor:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def analyze(self, audio_data, sample_rate, context) -> SensorResult:
        raise NotImplementedError

# registry.py
class SensorRegistry:
    def __init__(self):
        self._sensors = {}

    def register(self, sensor: BaseSensor):
        self._sensors[sensor.name] = sensor

    def analyze_all(self, audio_data, sample_rate, context) -> List[SensorResult]:
        return [s.analyze(audio_data, sample_rate, context)
                for s in self._sensors.values()]
```

**Benefits:**
- Easy to add new sensors
- Modular testing
- Configuration-driven weights
- No code changes to add/remove sensors

### Multi-Stage Detection Pipeline

6 sequential stages with early termination:

```
1. Feature Extraction → 2. Temporal Analysis → 3. Artifact Detection
     ↓                        ↓                       ↓
4. Neural Detection (RawNet3) → 5. Physics Analysis (Sensors) → 6. Fusion Engine
                                                                      ↓
                                                                  Final Verdict
```

Each stage can veto (mark as FAKE) and stop the pipeline early.

### MFA Decision Engine

Risk-adaptive authentication:

```python
def authenticate(context: TransactionContext, factors: AuthenticationFactors):
    # 1. Evaluate each factor
    voice_result = evaluate_voice(factors.voice)
    device_result = evaluate_device(factors.device)
    behavioral_result = evaluate_behavioral(factors.behavioral)

    # 2. Calculate risk score
    risk_score = calculate_risk(context, [voice_result, device_result])

    # 3. Make decision based on policy
    if risk_score < policy.low_risk_threshold:
        return {"decision": "APPROVE", "risk": "low"}
    elif risk_score < policy.high_risk_threshold:
        return {"decision": "STEP_UP", "risk": "medium"}
    else:
        return {"decision": "DENY", "risk": "high"}
```

### Async Processing with Celery

Long-running tasks (detection, transcription) use Celery:

```python
# tasks/detection.py
@celery_app.task(bind=True)
def analyze_audio_task(self, audio_path: str, config: dict):
    # Update task state
    self.update_state(state='PROGRESS', meta={'progress': 0.1})

    # Run detection pipeline
    result = detection_pipeline.run(audio_path, config)

    self.update_state(state='PROGRESS', meta={'progress': 1.0})
    return result

# api/detection_router.py
@router.post("/detect/async")
async def detect_async(file: UploadFile):
    task = analyze_audio_task.delay(file_path, config)
    return {"job_id": task.id, "status": "processing"}

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    task = AsyncResult(job_id)
    return {"status": task.state, "result": task.result}
```

---

## Security Considerations

### Input Validation

**Always validate and sanitize inputs:**

```python
# backend/api/validation.py
def validate_transaction_id(transaction_id: str) -> bool:
    """Prevent SQL injection in transaction IDs."""
    if not re.match(r'^[a-zA-Z0-9_-]{1,100}$', transaction_id):
        raise ValueError("Invalid transaction_id format")
    return True

def sanitize_user_input(text: str) -> str:
    """Remove potential XSS vectors."""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    return text
```

### Rate Limiting

Protect endpoints from abuse:

```python
# In api/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@app.post("/api/authenticate")
@limiter.limit("50/minute")  # 50 requests per minute
async def authenticate(request: Request, ...):
    # ...
```

### API Authentication

Production deployments should require API keys:

```python
# In api/middleware.py
async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### Secrets Management

**Never commit secrets to git:**

```bash
# Use .env for local development
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# Use environment variables in production
# Set via Docker, Kubernetes, or hosting platform
```

### CORS Configuration

Configure allowed origins in production:

```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Not "*" in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Optimization

### Rust Sensors for Performance

High-performance operations use Rust:

```rust
// sonotheia_rust/src/sensors/vacuum_sensor.rs
#[pyfunction]
pub fn analyze_vacuum(audio: Vec<f32>, sample_rate: u32) -> PyResult<VacuumResult> {
    // Fast FFT and spectral analysis in Rust
    // 10-100x faster than pure Python
}
```

Called from Python:
```python
from sonotheia_rust import analyze_vacuum

result = analyze_vacuum(audio_data.tolist(), sample_rate)
```

### Caching Strategies

```python
# Cache expensive computations
from functools import lru_cache

@lru_cache(maxsize=128)
def compute_features(audio_hash: str):
    # Expensive feature extraction
    pass

# Use Redis for distributed caching
import redis
cache = redis.Redis(host='redis', port=6379)

def get_detection_result(audio_hash):
    cached = cache.get(f"detection:{audio_hash}")
    if cached:
        return json.loads(cached)

    result = run_detection(audio_hash)
    cache.setex(f"detection:{audio_hash}", 3600, json.dumps(result))
    return result
```

### Database Queries

When adding database support:

```python
# Use async queries
from databases import Database

database = Database("postgresql://...")

async def get_user_profile(user_id: str):
    query = "SELECT * FROM users WHERE id = :id"
    return await database.fetch_one(query, values={"id": user_id})

# Index frequently queried fields
# CREATE INDEX idx_users_id ON users(id);
```

---

## Debugging Guide

### Backend Debugging

**Check logs:**
```bash
# Docker logs
docker compose logs backend -f
docker compose logs celery_worker -f

# Local development
# Logs appear in terminal running uvicorn
```

**Test individual components:**
```bash
cd backend

# Test a specific sensor
python -c "
from sensors.glottal_inertia import GlottalInertiaSensor
import numpy as np
sensor = GlottalInertiaSensor()
audio = np.random.randn(16000)  # 1 second of noise
result = sensor.analyze(audio, 16000, {})
print(result)
"

# Test detection pipeline
python scripts/test_pipeline.py

# Test API endpoint manually
curl http://localhost:8000/api/v1/health
```

**Python debugger:**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use Python 3.7+ built-in
breakpoint()
```

**Check module status:**
```bash
python scripts/ci_verify_operability.py
```

### Frontend Debugging

**Browser DevTools:**
- Console: Check for JavaScript errors
- Network: Inspect API requests/responses
- React DevTools: Inspect component state

**Check API connectivity:**
```javascript
// In browser console
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)
```

**Common issues:**
```bash
# Backend not responding
curl http://localhost:8000/
# If fails, check backend logs

# CORS errors
# Check CORS middleware in backend/api/main.py

# Module not found errors
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Celery/Redis Debugging

**Check Redis:**
```bash
docker compose exec redis redis-cli ping
# Should return: PONG

# List queues
docker compose exec redis redis-cli KEYS '*'
```

**Flower monitoring:**
```
Open browser: http://localhost:5555
- View active tasks
- Check worker status
- Monitor task history
```

**Celery worker logs:**
```bash
docker compose logs celery_worker -f
```

### Performance Debugging

**Profile Python code:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = detection_pipeline.run(audio_path)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Measure API response times:**
```bash
# Using httpx-cli (install: pip install httpx-cli)
time httpx POST http://localhost:8000/api/authenticate ...

# Check X-Response-Time header
curl -I http://localhost:8000/api/v1/health
```

---

## Integration Points

### Incode Integration

Sonotheia integrates with Incode Omni for biometric onboarding:

```python
# Workflow:
# 1. Incode performs face/ID verification
# 2. Incode triggers Sonotheia voice authentication
# 3. Sonotheia returns risk score
# 4. Incode combines scores for final decision

# See: Documentation/Guides/INCODE_INTEGRATION_GUIDE.md
```

### External API Integration

**Adding new integrations:**

```python
# backend/integrations/my_service.py
import httpx

class MyServiceClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def verify_user(self, user_id: str) -> dict:
        response = await self.client.post(
            f"{self.base_url}/verify",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()

# Use in API routes
from backend.integrations.my_service import MyServiceClient

@router.post("/verify-with-service")
async def verify_with_service(user_id: str):
    client = MyServiceClient(api_key=settings.MY_SERVICE_API_KEY)
    try:
        result = await client.verify_user(user_id)
        return result
    finally:
        await client.close()
```

### Webhook Support

**Receiving webhooks:**

```python
# backend/api/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/incode")
async def handle_incode_webhook(request: Request):
    # Verify signature
    signature = request.headers.get("X-Incode-Signature")
    payload = await request.body()

    if not verify_signature(payload, signature, settings.INCODE_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook
    data = await request.json()
    event_type = data.get("event")

    if event_type == "verification.completed":
        # Handle verification completion
        user_id = data["user_id"]
        # Trigger Sonotheia analysis

    return {"status": "received"}
```

---

## Deployment

### Docker Production Deployment

**Build and deploy:**
```bash
# Production docker-compose
docker compose -f docker-compose.prod.yml up -d

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale celery_worker=3

# Check status
docker compose ps

# View logs
docker compose logs -f --tail=100

# Update deployment
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Environment-Specific Configuration

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - DEMO_MODE=false
      - LOG_LEVEL=WARNING
      - API_KEYS=${API_KEYS}
    restart: always

  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD}
```

### Health Checks

**Backend health:**
```bash
curl http://localhost:8000/api/v1/health
# Returns: {"status": "healthy", "version": "..."}
```

**Docker health checks:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Monitoring

**Prometheus metrics:**
```
# Available at /metrics endpoint
# Counter: api_requests_total
# Histogram: api_request_duration_seconds
# Gauge: celery_active_tasks
```

**Logging:**
```python
# Structured logging
import logging

logger = logging.getLogger(__name__)
logger.info("Processing request", extra={
    "request_id": request_id,
    "user_id": user_id,
    "duration": duration
})
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to develop, PR to main | Linting, smoke tests |
| `operability.yml` | PR, manual | Full integration tests |
| `ops-check.yml` | Daily, config changes | Module status check |
| `branch-protection-check.yml` | PR to main | Verify branch protection |
| `lfs-check.yml` | Push, PR | Git LFS verification |

### Running CI Locally

```bash
# Smoke test
cd backend
python -c "from api.main import app; print('✓ Imports successful')"

# Linting
black --check backend
flake8 backend

# Operability check
python scripts/ci_verify_operability.py

# Full test suite
pytest

# Frontend lint
cd frontend && npm run lint
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Common Pitfalls & Solutions

### 1. Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'backend'`

**Solution:**
```bash
# Ensure you're in the correct directory
cd /home/user/sonotheia-enhanced/backend

# Verify PYTHONPATH
export PYTHONPATH=/home/user/sonotheia-enhanced:$PYTHONPATH

# Or use relative imports within backend/
from .sensors.base import BaseSensor  # Within backend package
```

### 2. Audio File Format Issues

**Problem:** `Error loading audio file: Unsupported format`

**Solution:**
```python
# Use soundfile for loading
import soundfile as sf

audio_data, sample_rate = sf.read(audio_path)

# Convert to numpy array if needed
import numpy as np
audio_data = np.array(audio_data, dtype=np.float32)

# Resample if needed
from scipy import signal
if sample_rate != target_rate:
    audio_data = signal.resample(audio_data,
                                  int(len(audio_data) * target_rate / sample_rate))
```

### 3. Celery Tasks Not Running

**Problem:** Tasks submitted but never executed

**Solution:**
```bash
# Check Redis connection
docker compose exec redis redis-cli ping

# Check worker logs
docker compose logs celery_worker

# Verify worker is consuming from correct queue
# In celery_worker logs, look for:
# [tasks] Registered tasks:
#   - backend.tasks.detection.analyze_audio_task

# Restart worker
docker compose restart celery_worker
```

### 4. Frontend CORS Errors

**Problem:** `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution:**
```python
# backend/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Sensor Threshold Issues

**Problem:** All audio marked as fake/real regardless of quality

**Solution:**
```bash
# Recalibrate sensors with known good samples
python backend/scripts/calibrate_library.py \
  --real-samples /path/to/real \
  --fake-samples /path/to/fake \
  --profile default

# Check calibration results in:
# backend/data/calibration/report.json

# Update thresholds in settings.yaml based on report
```

### 6. Docker Build Failures

**Problem:** `ERROR [backend 5/8] RUN pip install -r requirements.txt`

**Solution:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild with no cache
docker compose build --no-cache

# Check requirements.txt for conflicts
pip install -r backend/requirements.txt  # Test locally

# Update pinned versions if needed
```

---

## Quick Reference Commands

### Development

```bash
# Start everything
./start.sh

# Stop everything
./stop.sh

# Backend only
cd backend && uvicorn api.main:app --reload

# Frontend only
cd frontend && npm start

# Run tests
cd backend && pytest
cd frontend && npm test

# Format code
black backend
npm run lint --fix  # (if configured)

# Check logs
docker compose logs -f backend
docker compose logs -f celery_worker
```

### Testing

```bash
# Quick pipeline test
python backend/scripts/test_pipeline.py

# Benchmark
python backend/scripts/run_benchmark.py

# Calibration
python backend/scripts/calibrate_library.py

# CI check
python scripts/ci_verify_operability.py

# Specific test
pytest backend/tests/test_api.py::test_authentication -v
```

### Docker

```bash
# Build and start
docker compose up --build

# Detached mode
docker compose up -d

# Stop
docker compose down

# Stop and remove volumes
docker compose down -v

# Restart service
docker compose restart backend

# View logs
docker compose logs -f backend

# Execute command in container
docker compose exec backend python scripts/test_pipeline.py

# Scale workers
docker compose up -d --scale celery_worker=3
```

### Git

```bash
# Check status
git status

# Commit changes
git add .
git commit -m "feat: Add new feature"

# Push (with retries for network issues)
git push -u origin claude/your-branch-name

# Pull latest
git pull origin claude/your-branch-name

# View recent commits
git log --oneline -10
```

---

## Additional Resources

### Documentation

- **Main README**: `/README.md` - Project overview and quick start
- **Architecture Reference**: `/Documentation/ARCHITECTURE_REFERENCE.md` - Complete architecture
- **API Documentation**: http://localhost:8000/docs (when running)
- **Patent Compliance**: `/Documentation/PATENT_COMPLIANCE.md` - Legal analysis
- **Incode Integration**: `/Documentation/Guides/INCODE_INTEGRATION_GUIDE.md`
- **MVP Guide**: `/backend/MVP_README.md` - MVP usage
- **Hybrid OOP/FP Guide**: `/reusable-components/HYBRID_OOP_FP_GUIDE.md`

### Code Examples

- **Sensors**: `/backend/sensors/` - Sensor implementations
- **API Routes**: `/backend/api/routes/` - Route handlers
- **React Components**: `/frontend/src/components/` - UI components
- **Tests**: `/backend/tests/` - Comprehensive test examples
- **Scripts**: `/backend/scripts/` - Automation scripts

### External Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Material-UI**: https://mui.com/
- **Celery**: https://docs.celeryq.dev/
- **Plotly**: https://plotly.com/javascript/
- **PyTorch**: https://pytorch.org/docs/

---

## Getting Help

### Debugging Checklist

When something goes wrong:

1. **Check logs** (most issues show up here)
   ```bash
   docker compose logs -f
   ```

2. **Verify services are running**
   ```bash
   docker compose ps
   ```

3. **Test backend health**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. **Check module configuration**
   ```bash
   cat modules.yaml
   python scripts/ci_verify_operability.py
   ```

5. **Review recent changes**
   ```bash
   git log --oneline -5
   git diff HEAD~1
   ```

6. **Run tests**
   ```bash
   pytest backend/tests/ -v
   ```

7. **Check environment variables**
   ```bash
   cat .env
   ```

### Common Error Messages

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| `ModuleNotFoundError` | Import path issue | Check PYTHONPATH, verify directory |
| `Connection refused` | Service not running | Start service, check docker-compose |
| `Rate limit exceeded` | Too many requests | Wait or adjust rate limits |
| `Invalid API key` | Missing/wrong API key | Check .env file |
| `Audio format not supported` | Wrong file format | Convert to WAV 16kHz mono |
| `Sensor threshold not found` | Missing config | Check settings.yaml |
| `Task timeout` | Long-running task | Increase timeout, check worker logs |

---

## AI Assistant Best Practices

### When Working on This Codebase

1. **Always read before writing**
   - Read the file you're about to modify
   - Understand existing patterns
   - Follow established conventions

2. **Use the reusable components library**
   - Check `/reusable-components/` before creating new utilities
   - Extend existing patterns rather than creating new ones

3. **Test your changes**
   - Run relevant tests: `pytest backend/tests/test_X.py`
   - Add new tests for new functionality
   - Verify with manual testing

4. **Update configuration**
   - Add new sensors to `settings.yaml`
   - Update `modules.yaml` if adding modules
   - Document new environment variables

5. **Follow the architecture**
   - Extend `BaseSensor` for new sensors
   - Use `SensorRegistry` for registration
   - Follow the 6-stage detection pipeline
   - Use Pydantic models for API schemas

6. **Write clear commit messages**
   - Use conventional commits (feat:, fix:, docs:, etc.)
   - Explain why, not just what
   - Reference issues if applicable

7. **Document as you go**
   - Update docstrings
   - Add comments for complex logic
   - Update README if adding features

8. **Security first**
   - Validate all inputs
   - Sanitize user data
   - Never commit secrets
   - Use rate limiting for new endpoints

### Questions to Ask Before Making Changes

- [ ] Have I read the existing code?
- [ ] Do I understand the current architecture?
- [ ] Is there an existing pattern I should follow?
- [ ] Will this break existing functionality?
- [ ] Do I need to update configuration files?
- [ ] Do I need to add tests?
- [ ] Will this require documentation updates?
- [ ] Are there security implications?
- [ ] Is this change following the established conventions?

---

**Last Updated**: 2025-12-10
**Maintained by**: doronpers
**For AI Assistants**: This guide is specifically designed for you. Follow these patterns, reference these files, and when in doubt, read the code first!
