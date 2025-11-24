# Reusable Code Catalog & Synthesis

## Executive Summary

This document catalogs reusable code patterns, test utilities, and UI/UX components from the Website-Sonotheia-v251120 repository and references to other implementations documented in IMPLEMENTATION_COMPARISON.md.

---

## 1. Backend Architecture Patterns

### 1.1 Sensor Architecture (Highly Reusable)

#### Base Sensor Pattern
**Location**: `backend/sensors/base.py`

**Reusability**: ⭐⭐⭐⭐⭐ Excellent

**Pattern Description**:
- Abstract base class for extensible sensor system
- Standardized `SensorResult` dataclass for consistent output
- Built-in validation and JSON serialization
- Type-safe with numpy array handling

**Key Components**:
```python
@dataclass
class SensorResult:
    sensor_name: str
    passed: Optional[bool]  # Supports pass/fail and info-only sensors
    value: float
    threshold: float
    reason: Optional[str]
    detail: Optional[str]
    metadata: Optional[Dict[str, Any]]
```

**Reuse Recommendations**:
- Use for ANY plugin-based detection/analysis system
- Adapt for image analysis, text analysis, security scanning
- Pattern supports both binary (pass/fail) and informational sensors

---

### 1.2 Sensor Registry Pattern
**Location**: `backend/sensors/registry.py`

**Reusability**: ⭐⭐⭐⭐⭐ Excellent

**Pattern Description**:
- Centralized sensor management system
- Dynamic sensor registration/unregistration
- Ordered execution with error handling
- Verdict aggregation logic

**Key Features**:
```python
class SensorRegistry:
    def register(sensor, name)
    def analyze_all(audio_data, samplerate, sensor_names=None)
    def get_verdict(results, fail_on_any=True)
```

**Reuse Recommendations**:
- Plugin architecture for any analysis pipeline
- Microservice orchestration
- Multi-stage validation systems
- Quality control pipelines

---

### 1.3 Concrete Sensor Implementations

#### Breath Sensor
**Location**: `backend/sensors/breath.py`
**Purpose**: Detects biologically impossible phonation patterns
**Algorithm**: Silence detection + phonation duration tracking
**Threshold**: 14 seconds max phonation

#### Dynamic Range Sensor
**Location**: `backend/sensors/dynamic_range.py`
**Purpose**: Detects compression artifacts
**Algorithm**: Crest factor (peak/RMS ratio)
**Threshold**: > 12 for natural audio

#### Bandwidth Sensor
**Location**: `backend/sensors/bandwidth.py`
**Purpose**: Frequency spectrum analysis
**Algorithm**: Spectral rolloff at 90th percentile
**Threshold**: 4000 Hz for fullband classification

**Reuse Pattern**: All sensors follow the same structure - can be templates for creating new sensors

---

## 2. Test Architecture Patterns

### 2.1 Comprehensive Test Structure
**Location**: `backend/test_main.py` (1137 lines)

**Reusability**: ⭐⭐⭐⭐ Very Good

**Test Categories**:
1. **Unit Tests per Sensor** (lines 58-382)
   - Success cases
   - Failure cases
   - Edge cases (empty, silence, boundaries)
   
2. **API Endpoint Tests** (lines 384-627)
   - Success scenarios
   - Error handling
   - Input validation
   - File handling

3. **Integration Tests** (lines 665-785)
   - Multi-sensor coordination
   - Verdict logic
   - Consistency checks

4. **Performance Tests** (lines 934-965)
   - Large file handling
   - Processing time validation
   - Float32 optimization tests

5. **Monitoring Tests** (lines 967-1134)
   - Health checks
   - Metrics endpoints
   - Prometheus format validation

**Reusable Test Patterns**:

#### Helper Function Pattern
```python
def create_audio_file(audio_data, samplerate=16000, format='wav'):
    """Helper to create audio file in memory"""
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, samplerate, format=format)
    buffer.seek(0)
    return buffer
```

#### Boundary Testing Pattern
```python
def test_edge_case_exactly_at_threshold(self):
    """Test edge case with value exactly at threshold"""
    # Should pass when exactly at threshold (<=)
    assert result["passed"] is True
    assert result["value"] <= threshold

def test_edge_case_just_over_threshold(self):
    """Test edge case with value just over threshold"""
    assert result["passed"] is False
    assert result["value"] > threshold
```

#### Error Testing Pattern
```python
def test_failure_invalid_audio_file(self, client):
    """Test failure with invalid audio file"""
    invalid_file = io.BytesIO(b"not an audio file")
    response = client.post(...)
    assert response.status_code == 400
    assert "error" in response.json()["detail"].lower()
```

---

### 2.2 Minimal Test Structure
**Location**: `backend/tests/test_sensors.py` (347 lines)

**Reusability**: ⭐⭐⭐⭐⭐ Excellent

**Advantages**:
- Cleaner, more focused tests
- Better test organization
- Uses pytest fixtures effectively
- Helper function pattern for backward compatibility

**Key Pattern - Backward Compatibility Wrappers**:
```python
def check_breath_sensor(audio_data, samplerate):
    """Helper function for backward compatibility with tests."""
    result = breath_sensor.analyze(audio_data, samplerate)
    return result.to_dict()
```

**Reuse Recommendations**:
- Use this test structure for new projects
- Cleaner than test_main.py
- Better maintainability

---

## 3. Frontend UI/UX Patterns

### 3.1 React Component Architecture
**Location**: `frontend/src/components/`

**Reusability**: ⭐⭐⭐⭐ Very Good

**Component Structure**:
```
components/
├── Navbar.jsx      - Navigation component
├── Hero.jsx        - Landing section
├── About.jsx       - Info section
├── Technology.jsx  - Feature showcase
├── Demo.jsx        - Interactive demo (most complex)
├── Contact.jsx     - Contact section
└── Footer.jsx      - Footer component
```

**Key Pattern - Simple Functional Components**:
```jsx
const Hero = () => (
  <section id="home" className="hero">
    <div className="hero-content">
      <h1 className="hero-title">True Voice. Verified.</h1>
      <p className="hero-subtitle">...</p>
      <a href="#demo" className="cta-button">Try A Demo</a>
    </div>
  </section>
);
```

---

### 3.2 Demo Component Pattern
**Location**: `frontend/src/components/Demo.jsx`

**Reusability**: ⭐⭐⭐⭐⭐ Excellent

**Key Features**:
- File upload with drag-and-drop
- Loading states
- Error handling
- Results display
- Environment-aware API configuration

**Reusable Patterns**:

#### API Configuration Pattern
```jsx
const apiBase = import.meta.env.VITE_API_BASE_URL?.length > 0
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")
    : "";
```

#### Upload State Management Pattern
```jsx
const [uploading, setUploading] = useState(false);
const [result, setResult] = useState(null);
const [error, setError] = useState("");

const handleFiles = (files) => {
  setUploading(true);
  setResult(null);
  setError("");
  // ... fetch logic
};
```

#### Drag-and-Drop Pattern
```jsx
<div
  className={`upload-area ${isDragging ? "dragging" : ""}`}
  onClick={() => inputRef.current?.click()}
  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
  onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
  onDrop={(e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }}
>
```

#### Dynamic Evidence Rendering Pattern
```jsx
function renderEvidenceRows(evidence) {
  const rows = [];
  
  // Add core sensors
  if (bandwidth) rows.push({...});
  if (dynamicRange) rows.push({...});
  if (breath) rows.push({...});
  
  // Add optional sensors dynamically
  ["phase_coherence", "vocal_tract", "coarticulation"].forEach((key) => {
    const sensor = evidence[key];
    if (sensor) rows.push({...});
  });
  
  return rows.map((row) => <div key={row.label}>...</div>);
}
```

---

### 3.3 CSS Design System
**Location**: `frontend/src/styles.css`

**Reusability**: ⭐⭐⭐⭐ Very Good

**Design Tokens**:
```css
:root {
  color-scheme: dark;
  font-family: "Space Grotesk", system-ui, -apple-system;
  background-color: #05070d;
  color: #f4f6fb;
}
```

**Reusable CSS Patterns**:

#### Glassmorphism Cards
```css
.feature-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 1.2rem;
  padding: 1.8rem;
  backdrop-filter: blur(6px);
}
```

#### Gradient Buttons
```css
.cta-button {
  background: linear-gradient(120deg, #5b8eff, #8f6bff);
  box-shadow: 0 20px 40px rgba(91, 142, 255, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 25px 55px rgba(91, 142, 255, 0.35);
}
```

#### Status Color System
```css
.verdict-REAL {
  background: rgba(70, 190, 125, 0.15);
  border: 1px solid rgba(70, 190, 125, 0.3);
}

.verdict-SYNTHETIC {
  background: rgba(255, 94, 94, 0.15);
  border: 1px solid rgba(255, 94, 94, 0.3);
}

.value.pass { color: #61d5a3; }
.value.fail { color: #ff7b7b; }
```

---

### 3.4 Alternative HTML Implementation
**Location**: `frontend/html/index.html`, `frontend/html/script.js`

**Reusability**: ⭐⭐⭐ Good

**Advantages**:
- No build step required
- Vanilla JavaScript
- Self-contained in single HTML file
- Good for simple deployments

**Key Pattern - Embedded JavaScript**:
- Smooth scroll navigation
- Fetch API for backend communication
- DOM manipulation for results display
- Table-based evidence display vs grid layout

**Comparison**:
| Feature | React (src/) | HTML (html/) |
|---------|-------------|--------------|
| Build Required | Yes (Vite) | No |
| Dependencies | React, Vite | None |
| Type Safety | Possible with TS | No |
| Maintainability | Better | Good |
| Load Time | Faster (optimized) | Good |
| Best For | Complex apps | Simple sites |

---

## 4. API & Metrics Patterns

### 4.1 FastAPI Structure
**Location**: `backend/main.py`

**Reusability**: ⭐⭐⭐⭐ Very Good

**Key Patterns**:

#### Middleware Pattern
```python
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    metrics.record_request()
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        if isinstance(e, HTTPException):
            pass  # Already recorded
        else:
            metrics.record_error(500, type(e).__name__)
        raise
```

#### Custom Exception Handlers
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    metrics.record_error(exc.status_code, "HTTPException")
    return JSONResponse(...)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    metrics.record_error(500, type(exc).__name__)
    return JSONResponse(...)
```

---

### 4.2 Metrics Collection Pattern
**Location**: `backend/main.py` (lines 52-193)

**Reusability**: ⭐⭐⭐⭐⭐ Excellent

**Features**:
- Thread-safe with RLock
- Multiple metric types (counters, gauges, histograms)
- Circular buffers for recent data
- Prometheus-compatible export

**Key Pattern - Circular Buffers**:
```python
self._processing_times = deque(maxlen=1000)
self._file_sizes = deque(maxlen=1000)
self._recent_errors = deque(maxlen=100)
```

**Reuse Recommendations**:
- Drop-in metrics collector for any Python service
- Extend with additional metric types
- Perfect for microservices observability

---

## 5. Utility Functions & Helpers

### 5.1 NumPy Type Conversion
**Location**: `backend/main.py` (lines 37-49)

**Reusability**: ⭐⭐⭐⭐⭐ Excellent

```python
def convert_numpy_types(obj):
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    return obj
```

**Reuse**: Essential for any NumPy + JSON API

---

### 5.2 Audio Processing Utilities
**Location**: `backend/sensors/utils.py`

**Reusable Functions**:
- dB conversion utilities
- RMS calculation
- Signal windowing
- Spectral analysis helpers

---

## 6. Configuration & Deployment Patterns

### 6.1 Environment Configuration
**Location**: `render.yaml`, `docker-compose.yml`

**Pattern**: Environment-based configuration
```yaml
envVars:
  - key: VITE_API_BASE_URL
    value: https://sonotheia-backend.onrender.com
```

**Reuse**: Template for multi-service deployments

---

### 6.2 Docker Configuration
**Location**: `backend/Dockerfile`, `frontend/Dockerfile`

**Key Patterns**:
- Multi-stage builds
- Non-root user
- Health checks
- Proper signal handling with entrypoint scripts

---

## 7. Documentation Patterns

### 7.1 Implementation Comparison
**Location**: `IMPLEMENTATION_COMPARISON.md`

**Reusability**: ⭐⭐⭐⭐⭐ Excellent Template

**Structure**:
- Current implementation overview
- Alternative implementations
- Feature comparison tables
- Integration roadmap
- Next steps

**Reuse**: Perfect template for comparing architectural options

---

### 7.2 Deployment Guides
**Locations**: `DEPLOYMENT.md`, `RENDER_DEPLOYMENT.md`

**Key Patterns**:
- Step-by-step deployment instructions
- Environment configuration
- Troubleshooting sections
- Service health checks

---

## 8. Recommended Extractions

### 8.1 Create Reusable Library: "sensor-framework"

**Extract**:
- `backend/sensors/base.py`
- `backend/sensors/registry.py`
- Core sensor implementations as examples

**Package Structure**:
```
sensor-framework/
├── sensor_framework/
│   ├── __init__.py
│   ├── base.py          # Base sensor + SensorResult
│   ├── registry.py      # Sensor registry
│   └── utils.py         # Common utilities
├── examples/
│   ├── breath_sensor.py
│   ├── dynamic_range_sensor.py
│   └── bandwidth_sensor.py
└── tests/
```

**Use Cases**:
- Audio analysis systems
- Image quality analysis
- Security scanning
- Any plugin-based validation system

---

### 8.2 Create UI Component Library: "audio-demo-components"

**Extract**:
- Demo component pattern
- Upload area with drag-and-drop
- Results display
- Loading states
- Error handling

**Package Structure**:
```
audio-demo-components/
├── src/
│   ├── UploadArea.jsx
│   ├── ResultsDisplay.jsx
│   ├── EvidenceGrid.jsx
│   └── styles/
│       ├── upload.css
│       └── results.css
└── README.md
```

---

### 8.3 Create Test Utilities: "audio-test-utils"

**Extract**:
- Audio file generation helpers
- Test data generators
- Common test fixtures
- Assertion helpers

**Functions**:
```python
def create_audio_file(audio_data, samplerate, format)
def generate_sine_wave(frequency, duration, samplerate)
def generate_test_audio(duration, samplerate, characteristics)
```

---

## 9. Code Quality Observations

### Strengths
✅ Well-organized sensor architecture
✅ Comprehensive test coverage
✅ Clear separation of concerns
✅ Good error handling
✅ Thread-safe metrics collection
✅ Modern React patterns
✅ Responsive CSS design

### Improvement Opportunities
⚠️ Add TypeScript to React components
⚠️ Add API documentation (OpenAPI/Swagger)
⚠️ Add integration tests between frontend and backend
⚠️ Consider adding rate limiting
⚠️ Add request ID tracking for debugging

---

## 10. Integration Recommendations

Based on IMPLEMENTATION_COMPARISON.md:

### Priority 1: Backend Enhancements
1. **Add Phase Coherence Sensor** from RecApp
2. **Add Vocal Tract Analyzer** from RecApp
3. **Add Coarticulation Analyzer** from RecApp

### Priority 2: Performance
1. **Consider Rust sensors** from SonoCheck for performance-critical sensors
2. **Add async processing** for large files

### Priority 3: Frontend
1. **Migrate to TypeScript** for type safety
2. **Add more interactive visualizations**
3. **Implement websono components** for professional UI

---

## Conclusion

This codebase contains several highly reusable patterns:

**Most Reusable (⭐⭐⭐⭐⭐)**:
1. Sensor base architecture + registry pattern
2. Metrics collection system
3. Demo component with upload/results pattern
4. NumPy JSON serialization utility
5. Test utility patterns

**Recommended Next Steps**:
1. Extract sensor framework into separate package
2. Create UI component library
3. Document APIs with OpenAPI
4. Add TypeScript support
5. Create example integrations

---

*Generated: 2025-11-23*
*Repository: Website-Sonotheia-v251120*
