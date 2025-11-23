# API Patterns - Reusable FastAPI Patterns

## Overview

Production-ready API patterns combining FastAPI framework (OOP) with functional transformations for robust, maintainable APIs.

## Core Patterns

### 1. Middleware for Cross-Cutting Concerns

#### Metrics Middleware (Hybrid Pattern)

```python
from fastapi import FastAPI, Request
from typing import Callable
import time

app = FastAPI()

# Functional: Middleware as higher-order function
@app.middleware("http")
async def metrics_middleware(request: Request, call_next: Callable):
    """
    Hybrid middleware:
    - OOP: FastAPI decorator pattern
    - FP: Request/response pipeline
    """
    # Record request (side effect)
    metrics.record_request()
    start_time = time.time()
    
    try:
        # Functional pipeline
        response = await call_next(request)
        
        # Calculate metrics (pure)
        processing_time = time.time() - start_time
        
        # Record success (side effect)
        metrics.record_processing(processing_time)
        
        return response
    except Exception as e:
        # Error handling (side effect)
        metrics.record_error(500, type(e).__name__)
        raise
```

#### Logging Middleware

```python
import logging
from fastapi import Request, Response

logger = logging.getLogger(__name__)

@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable):
    """Log all requests/responses"""
    # Functional: Extract request info
    request_info = {
        'method': request.method,
        'url': str(request.url),
        'client': request.client.host if request.client else None
    }
    
    logger.info(f"Request: {request_info}")
    
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise
```

---

### 2. Custom Exception Handlers (Hybrid)

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Pure function: Error response builder
def build_error_response(
    status_code: int,
    detail: str,
    request_path: str,
    error_type: str = "error"
) -> Dict[str, Any]:
    """Pure function: Build standardized error response"""
    return {
        "error": {
            "type": error_type,
            "status_code": status_code,
            "detail": detail,
            "path": request_path
        }
    }


# OOP: Exception handler registration
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Hybrid handler:
    - OOP: FastAPI exception handler
    - FP: Pure response builder
    """
    # Side effect: logging
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}"
    )
    
    # Side effect: metrics
    metrics.record_error(exc.status_code, "HTTPException")
    
    # Pure transformation
    error_response = build_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        request_path=request.url.path,
        error_type="http_error"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error(
        f"Unexpected error: {str(exc)} - Path: {request.url.path}",
        exc_info=True
    )
    
    metrics.record_error(500, type(exc).__name__)
    
    # Don't expose internal errors
    error_response = build_error_response(
        status_code=500,
        detail="Internal server error. Please try again later.",
        request_path=request.url.path,
        error_type="server_error"
    )
    
    return JSONResponse(status_code=500, content=error_response)
```

---

### 3. Request Validation (Functional Pattern)

```python
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException
import numpy as np

# Pure validation functions
def validate_file_size(
    file_size: int,
    max_size_mb: int = 50
) -> Tuple[bool, Optional[str]]:
    """Pure function: Validate file size"""
    max_bytes = max_size_mb * 1024 * 1024
    
    if file_size == 0:
        return False, "Empty file uploaded"
    
    if file_size > max_bytes:
        return False, f"File too large. Maximum size is {max_size_mb}MB"
    
    return True, None


def validate_content_type(
    content_type: Optional[str],
    allowed_types: List[str] = ["audio/"]
) -> Tuple[bool, Optional[str]]:
    """Pure function: Validate content type"""
    if not content_type:
        return True, None  # Allow missing content-type
    
    if not any(content_type.startswith(t) for t in allowed_types):
        return False, f"Invalid file type. Expected audio file, got {content_type}"
    
    return True, None


def validate_audio_properties(
    audio_data: np.ndarray,
    samplerate: int,
    min_samplerate: int = 8000,
    max_samplerate: int = 192000,
    max_duration_seconds: float = 300.0
) -> Tuple[bool, Optional[str]]:
    """Pure function: Validate audio properties"""
    # Validate samplerate
    if samplerate < min_samplerate or samplerate > max_samplerate:
        return False, (
            f"Invalid sample rate: {samplerate}Hz. "
            f"Must be between {min_samplerate}Hz and {max_samplerate}Hz"
        )
    
    # Validate duration
    duration = len(audio_data) / samplerate
    if duration > max_duration_seconds:
        return False, (
            f"Audio too long: {duration:.1f}s. "
            f"Maximum duration is {max_duration_seconds}s"
        )
    
    return True, None


# Functional composition of validators
def validate_upload(
    file: UploadFile,
    file_content: bytes,
    audio_data: np.ndarray,
    samplerate: int
) -> None:
    """
    Compose all validations.
    Raises HTTPException on validation failure.
    """
    # File size validation
    valid, error = validate_file_size(len(file_content))
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Content type validation
    valid, error = validate_content_type(file.content_type)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Audio properties validation
    valid, error = validate_audio_properties(audio_data, samplerate)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
```

---

### 4. Response Builders (Pure Functions)

```python
from typing import Dict, Any
import numpy as np

def convert_numpy_types(obj: Any) -> Any:
    """Pure function: Recursive numpy → JSON conversion"""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def build_success_response(
    verdict: str,
    detail: str,
    evidence: Dict[str, Any],
    processing_time: float,
    model_version: str
) -> Dict[str, Any]:
    """Pure function: Build success response"""
    response = {
        "verdict": verdict,
        "detail": detail,
        "processing_time_seconds": round(processing_time, 3),
        "model_version": model_version,
        "evidence": evidence
    }
    
    # Convert numpy types for JSON serialization
    return convert_numpy_types(response)


def build_analysis_metadata(
    file_size_mb: float,
    samplerate: int,
    duration_seconds: float,
    num_channels: int
) -> Dict[str, Any]:
    """Pure function: Build metadata"""
    return {
        "file_size_mb": round(file_size_mb, 2),
        "samplerate": samplerate,
        "duration_seconds": round(duration_seconds, 2),
        "channels": num_channels
    }
```

---

### 5. Endpoint Pattern (Hybrid: OOP + FP Pipeline)

```python
from fastapi import FastAPI, File, UploadFile, HTTPException
import io
import time
import soundfile as sf

app = FastAPI(
    title="Audio Analysis API",
    version="1.0.0",
    description="Physics-based audio authenticity detection"
)

@app.post("/api/v2/detect/quick", tags=["Detection"])
async def quick_detect(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Hybrid endpoint:
    - OOP: FastAPI framework, route decorator
    - FP: Functional transformation pipeline
    """
    start_time = time.time()
    
    try:
        # === STAGE 1: File I/O (side effects) ===
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        # === STAGE 2: Validation (pure functions) ===
        validate_file_size(len(file_content))
        validate_content_type(file.content_type)
        
        # === STAGE 3: Audio I/O (side effect) ===
        try:
            audio_data, samplerate = sf.read(io.BytesIO(file_content))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read audio file: {str(e)}"
            )
        
        # === STAGE 4: Preprocessing (pure functions) ===
        audio_data = preprocess_audio(audio_data)
        validate_audio_properties(audio_data, samplerate)
        
        # === STAGE 5: Analysis (OOP sensors) ===
        sensor_results = sensor_registry.analyze_all(audio_data, samplerate)
        verdict, detail = sensor_registry.get_verdict(sensor_results)
        
        # === STAGE 6: Response building (pure functions) ===
        processing_time = time.time() - start_time
        
        evidence_payload = {
            name: result.to_dict()
            for name, result in sensor_results.items()
        }
        
        response = build_success_response(
            verdict=verdict,
            detail=detail,
            evidence=evidence_payload,
            processing_time=processing_time,
            model_version="v9.0"
        )
        
        # === STAGE 7: Metrics (side effect) ===
        metrics.record_processing(processing_time, file_size_mb, verdict)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed")
```

---

### 6. Health Check Endpoints (Functional Pattern)

```python
from datetime import datetime
from typing import Dict, Any

# Pure functions for health check data
def build_health_response(
    status: str,
    service_name: str,
    version: str,
    uptime_seconds: float
) -> Dict[str, Any]:
    """Pure function: Build health check response"""
    return {
        "status": status,
        "service": service_name,
        "version": version,
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health Check"])
def health_check() -> Dict[str, Any]:
    """Detailed health check endpoint"""
    # Get metrics snapshot (functional)
    stats = metrics.get_stats()
    
    # Build response (pure)
    return {
        "status": "healthy",
        "service": "Audio Analysis API",
        "version": "v9.0",
        "uptime_seconds": stats["uptime_seconds"],
        "requests": {
            "total": stats["requests"]["total"],
            "success": stats["requests"]["success"],
            "errors": stats["requests"]["errors"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/", tags=["Health Check"])
def root() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "ok",
        "service": "Audio Analysis API",
        "version": "v9.0"
    }
```

---

### 7. Monitoring Endpoints (Functional Transformation)

```python
from fastapi import Response

@app.get("/metrics", tags=["Monitoring"])
def get_prometheus_metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Functional pipeline: snapshot → transform → format
    """
    # Get snapshot (OOP)
    metrics_text = metrics.get_prometheus_metrics()
    
    # Return with proper content type
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4"
    )


@app.get("/stats", tags=["Monitoring"])
def get_stats() -> Dict[str, Any]:
    """
    Application statistics endpoint.
    
    Pure transformation of metrics snapshot.
    """
    # Get snapshot
    stats = metrics.get_stats()
    
    # Add timestamp (pure)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": stats
    }
```

---

### 8. CORS Configuration (OOP Pattern)

```python
from fastapi.middleware.cors import CORSMiddleware

# Configuration as data (functional)
ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:3000",
    "https://sonotheia.ai",
    "https://www.sonotheia.ai",
    "https://sonotheia-frontend.onrender.com",
]

# Apply middleware (OOP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Security: disable for APIs
    allow_methods=["GET", "POST"],  # Only necessary methods
    allow_headers=["Content-Type", "Authorization"],
)
```

---

### 9. Dependency Injection (Functional Pattern)

```python
from fastapi import Depends
from typing import Generator

# Functional: Generator for dependencies
def get_sensor_registry() -> Generator[SensorRegistry, None, None]:
    """Dependency: Sensor registry"""
    yield sensor_registry


def get_metrics() -> Generator[MetricsCollector, None, None]:
    """Dependency: Metrics collector"""
    yield metrics


# Use in endpoints
@app.post("/api/analyze")
async def analyze(
    file: UploadFile,
    registry: SensorRegistry = Depends(get_sensor_registry),
    metrics: MetricsCollector = Depends(get_metrics)
):
    """Endpoint with dependency injection"""
    # Use injected dependencies
    results = registry.analyze_all(audio_data, samplerate)
    metrics.record_request()
    return results
```

---

### 10. API Versioning Pattern

```python
from fastapi import APIRouter

# Create version-specific routers
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

# V1 endpoints
@v1_router.post("/detect")
async def detect_v1(file: UploadFile):
    """Legacy detection endpoint"""
    return {"version": "v1", "result": "..."}

# V2 endpoints
@v2_router.post("/detect/quick")
async def detect_v2(file: UploadFile):
    """Enhanced detection endpoint"""
    return {"version": "v2", "result": "..."}

# Include routers
app.include_router(v1_router)
app.include_router(v2_router)
```

---

## Complete API Example

```python
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="Audio Analysis API",
    version="1.0.0",
    description="Physics-based audio detection"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

# Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    metrics.record_request()
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        metrics.record_error(500, type(e).__name__)
        raise

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    metrics.record_error(exc.status_code, "HTTPException")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Health endpoints
@app.get("/")
def root():
    return {"status": "ok", "service": "Audio Analysis API"}

@app.get("/health")
def health():
    stats = metrics.get_stats()
    return {
        "status": "healthy",
        "uptime": stats["uptime_seconds"],
        "requests": stats["requests"]["total"]
    }

# Main endpoint
@app.post("/api/v2/detect/quick")
async def quick_detect(file: UploadFile = File(...)):
    start_time = time.time()
    
    # Read file
    file_content = await file.read()
    
    # Validate
    validate_upload(file, file_content)
    
    # Process
    audio_data, samplerate = read_audio(file_content)
    audio_data = preprocess_audio(audio_data)
    
    # Analyze
    results = sensor_registry.analyze_all(audio_data, samplerate)
    verdict, detail = sensor_registry.get_verdict(results)
    
    # Build response
    processing_time = time.time() - start_time
    response = build_success_response(
        verdict, detail, results, processing_time, "v9.0"
    )
    
    # Metrics
    metrics.record_processing(processing_time, len(file_content), verdict)
    
    return response
```

---

## Benefits

✅ **Separation of Concerns**: Clear boundaries between I/O, validation, business logic
✅ **Testability**: Pure functions easily tested, OOP endpoints mocked
✅ **Maintainability**: Functional pipeline is easy to follow
✅ **Error Handling**: Centralized exception handlers
✅ **Observability**: Built-in metrics and logging
✅ **Type Safety**: Full type hints throughout
✅ **Security**: Input validation, CORS configuration
✅ **Performance**: Async/await where needed

## License

Reusable under project license.
