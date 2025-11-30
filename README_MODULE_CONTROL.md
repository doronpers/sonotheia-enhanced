# Module Control Documentation

[![Modules Enabled](https://img.shields.io/endpoint?url=https%3A%2F%2F<PUBLIC_BASE_URL>%2Fapi%2Fbadge%2Fmodules_enabled&label=modules)](./README_MODULE_CONTROL.md)

This document describes the centralized module control system for Sonotheia Enhanced.

## Current Module Status

<!-- MODULE_STATUS_TABLE_START -->
| Module | Configured | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |
|--------|-----------|-----------|-------------------|--------------------|--------|
| audio | ✅ | ✅ | N/A | N/A | configured |
| analysis | ✅ | ✅ | N/A | N/A | configured |
| detection | ✅ | ✅ | N/A | N/A | configured |
| calibration | ✅ | ✅ | N/A | N/A | configured |
| transcription | ✅ | ✅ | N/A | N/A | configured |
| risk_engine | ✅ | ✅ | N/A | N/A | configured |
| sar | ✅ | ✅ | N/A | N/A | configured |
| rate_limiting | ✅ | ✅ | N/A | N/A | configured |
| celery | ✅ | ✅ | N/A | N/A | configured |
| observability | ✅ | ✅ | N/A | N/A | configured |
| tenants | ✅ | ✅ | N/A | N/A | configured |
| mlflow | ✅ | ✅ | N/A | N/A | configured |

*This table is auto-generated. Run `python scripts/generate_module_status_table.py` to update.*
<!-- MODULE_STATUS_TABLE_END -->

## Overview

The module registry provides a declarative way to enable/disable features at runtime through:
1. **Profile presets** (`MODULE_PROFILE=minimal|standard|full`) - Base configuration
2. **Configuration file** (`modules.yaml`) - Override profile defaults
3. **Environment variables** - Override YAML (highest precedence)
4. **Admin API endpoints** - Runtime toggling (non-persistent)

## Profile Presets

Profile presets provide predefined module sets for different deployment environments. Set via the `MODULE_PROFILE` environment variable.

### Available Profiles

| Profile | Modules Included |
|---------|------------------|
| `minimal` | audio, detection, sar, rate_limiting, observability |
| `standard` | minimal + calibration, analysis, celery |
| `full` | standard + transcription, tenants, mlflow, risk_engine |

### Using Profiles

```bash
# Use minimal profile for lightweight deployments
export MODULE_PROFILE=minimal

# Use standard profile (default if not specified)
export MODULE_PROFILE=standard

# Use full profile for all features
export MODULE_PROFILE=full
```

**Default**: If `MODULE_PROFILE` is not set, the system defaults to `full`.

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

## Prometheus Metrics

Module states are exported as Prometheus metrics for monitoring.

### Metrics Format

```
sonotheia_module_enabled{name="audio"} 1
sonotheia_module_enabled{name="detection"} 1
sonotheia_module_enabled{name="calibration"} 0
```

Values: `1` = enabled, `0` = disabled

### Accessing Metrics

```bash
# Get Prometheus metrics
curl http://localhost:8000/metrics

# Filter for module metrics
curl http://localhost:8000/metrics | grep sonotheia_module_enabled
```

### Metrics Refresh

Metrics are automatically updated:
- On application startup
- When the `/metrics` endpoint is called
- When `/api/admin/modules/recheck` is triggered

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
      "description": "Core audio processing...",
      "metrics_value": 1
    }
  ],
  "total": 12,
  "enabled_count": 10,
  "disabled_count": 2,
  "profile": "full",
  "available_profiles": {
    "minimal": {"modules": ["audio", "detection", "observability", "rate_limiting", "sar"], "module_count": 5},
    "standard": {"modules": [...], "module_count": 8},
    "full": {"modules": [...], "module_count": 12}
  }
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

### Force Health Recheck
```bash
POST /api/admin/modules/recheck
```

Triggers a health re-assessment and refreshes Prometheus metrics.

**Response**:
```json
{
  "message": "Module health recheck completed and metrics refreshed",
  "modules_updated": 12,
  "metrics": {
    "audio": 1,
    "detection": 1,
    "calibration": 0
  },
  "last_health_recheck": "2025-01-15T12:00:00Z"
}
```

### Module Summary
```bash
GET /api/admin/modules/summary
```

**Requires**: Admin-level API key

Quick summary of module states for dashboards and monitoring.

**Response**:
```json
{
  "total": 12,
  "enabled": 10,
  "disabled": 2,
  "last_recheck": "2025-01-15T12:00:00Z"
}
```

### Shields.io Badge Endpoint
```bash
GET /api/badge/modules_enabled
```

**No authentication required** - Lightweight endpoint for dynamic badges.

Returns Shields.io compatible JSON for embedding badges in documentation.

**Response**:
```json
{
  "schemaVersion": 1,
  "label": "modules",
  "message": "10/12",
  "color": "brightgreen"
}
```

**Color thresholds**:
- ≥80% enabled: `brightgreen`
- ≥50% enabled: `yellow`
- <50% enabled: `red`

**Usage in Markdown**:
```markdown
![Modules Enabled](https://img.shields.io/endpoint?url=https://YOUR_HOST/api/badge/modules_enabled)
```

### Prometheus Metrics Endpoint
```bash
GET /metrics
```

Returns Prometheus-formatted metrics including module states.

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

1. **Profile defaults** - `MODULE_PROFILE` selects base configuration (minimal/standard/full)
2. **YAML file** - `modules.yaml` configuration overrides profile defaults
3. **Environment variables** - `MODULE_<NAME>=0|1` overrides YAML
4. **Runtime API** - Admin API toggle (non-persistent, resets on restart)

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
