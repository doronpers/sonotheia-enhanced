# Module Control Documentation

This document describes the centralized module control system for Sonotheia Enhanced.

## Overview

The module registry provides a declarative way to enable/disable features at runtime through:
1. **Configuration file** (`modules.yaml`) - Default states
2. **Environment variables** - Override configuration (takes precedence)
3. **Admin API endpoints** - Runtime toggling (non-persistent)

## Configuration

### modules.yaml

The `modules.yaml` file at the repository root defines all modules and their default states:

```yaml
modules:
  audio:
    enabled: true
    description: "Core audio processing and loading functionality"

  detection:
    enabled: true
    description: "Deepfake and spoof detection capabilities"

  calibration:
    enabled: false
    description: "Audio calibration and preprocessing tools"

  # ... more modules
```

### Environment Variable Overrides

Environment variables override YAML configuration. Format: `MODULE_<NAME>=0|1`

```bash
# Disable calibration module
export MODULE_CALIBRATION=0

# Enable transcription module
export MODULE_TRANSCRIPTION=1
```

Valid values:
- Enable: `1`, `true`, `True`, `TRUE`, `yes`, `Yes`, `YES`
- Disable: `0`, `false`, `False`, `FALSE`, `no`, `No`, `NO`

## Managed Modules

The following modules can be controlled:

| Module | Description |
|--------|-------------|
| `audio` | Core audio processing and loading |
| `analysis` | Audio analysis and feature inspection |
| `detection` | Deepfake and spoof detection |
| `calibration` | Audio calibration and preprocessing |
| `transcription` | Speech-to-text transcription |
| `risk_engine` | Risk scoring and assessment |
| `sar` | Suspicious Activity Report generation |
| `rate_limiting` | API rate limiting |
| `celery` | Asynchronous task processing |
| `observability` | Logging, metrics, and tracing |
| `tenants` | Multi-tenant support |
| `mlflow` | ML experiment tracking |

## API Endpoints

### List All Modules
```bash
GET /api/admin/modules
```

**Requires**: Admin-level API key

**Response**:
```json
{
  "modules": [
    {
      "name": "audio",
      "enabled": true,
      "description": "Core audio processing..."
    }
  ],
  "total": 12,
  "enabled_count": 10,
  "disabled_count": 2
}
```

### Get Module Info
```bash
GET /api/admin/modules/{module_name}
```

### Toggle Module State
```bash
PUT /api/admin/modules/{module_name}
Content-Type: application/json

{
  "enabled": false
}
```

### Enable/Disable Shortcuts
```bash
POST /api/admin/modules/{module_name}/enable
POST /api/admin/modules/{module_name}/disable
```

## Using in Code

### Dependency Guard for Routes

Protect endpoints that require specific modules:

```python
from fastapi import Depends
from api.dependencies import require_module

@app.get("/api/calibration/status")
async def calibration_status(
    _: None = Depends(require_module("calibration"))
):
    # This endpoint returns 503 if calibration module is disabled
    return {"status": "operational"}
```

When the module is disabled, requests receive:
```json
HTTP 503 Service Unavailable
{
  "error_code": "MODULE_DISABLED",
  "message": "Module 'calibration' is currently disabled",
  "module": "calibration"
}
```

### Multiple Module Requirements

```python
from api.dependencies import require_all_modules, require_any_module

# Require ALL modules
@app.get("/api/full-analysis")
async def full_analysis(
    _: None = Depends(require_all_modules("audio", "detection", "risk_engine"))
):
    ...

# Require ANY ONE module
@app.get("/api/transcribe")
async def transcribe(
    _: None = Depends(require_any_module("transcription", "detection"))
):
    ...
```

### Checking Module State in Code

```python
from core.module_registry import is_module_enabled, get_registry

# Simple check
if is_module_enabled('calibration'):
    # Do calibration work
    pass

# Get full registry for multiple checks
registry = get_registry()
if registry.is_enabled('audio') and registry.is_enabled('detection'):
    # Process audio with detection
    pass
```

### Celery Task Checks

See `backend/tasks/_example_checks.txt` for patterns on respecting module state in async tasks.

```python
from celery import shared_task
from core.module_registry import is_module_enabled

@shared_task(bind=True)
def process_audio(self, audio_id: str):
    if not is_module_enabled('audio'):
        return {'status': 'skipped', 'reason': 'audio module disabled'}
    # Process audio...
```

## Docker Integration

### Docker Compose Override

```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - MODULE_CALIBRATION=0
      - MODULE_TRANSCRIPTION=0
    volumes:
      - ./custom-modules.yaml:/app/modules.yaml:ro
```

### Docker Run

```bash
docker run -e MODULE_CALIBRATION=0 \
           -e MODULE_TRANSCRIPTION=0 \
           -v $(pwd)/modules.yaml:/app/modules.yaml:ro \
           sonotheia-backend
```

## Precedence Order

Configuration is applied in this order (later overrides earlier):

1. **Default** - Unknown modules default to `enabled=true`
2. **YAML file** - `modules.yaml` configuration
3. **Environment variables** - `MODULE_<NAME>=0|1`
4. **Runtime API** - Admin API toggle (non-persistent)

## Security Considerations

1. **Admin API Access**: Module toggle endpoints require admin-level API key
2. **Rate Limiting**: Toggle endpoints have protective rate limits (20/minute)
3. **Audit Logging**: All module state changes are logged with admin identity
4. **Non-Persistent**: Runtime API changes reset on restart (intentional)

## Best Practices

1. **Use YAML for defaults**: Set baseline configuration in `modules.yaml`
2. **Use env vars for deployments**: Override per-environment via environment variables
3. **Use API for testing**: Toggle modules at runtime for testing scenarios
4. **Monitor disabled modules**: Watch logs for "module disabled" messages
5. **Document dependencies**: Note module requirements in endpoint documentation
