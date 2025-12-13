# Sonotheia Enhanced - System Status

> Live operational status of Sonotheia Enhanced platform modules and services

[![Ops Check](https://github.com/doronpers/sonotheia-enhanced/actions/workflows/ops-check.yml/badge.svg)](https://github.com/doronpers/sonotheia-enhanced/actions/workflows/ops-check.yml)

## Overview

This document provides the current operational status of all platform modules. The status table below is automatically updated by the CI/CD pipeline when changes are made to the module configuration or backend services.

<!-- MODULE_STATUS_TABLE_START -->

## Module Status

**Profile:** full | **Total:** 12 | **Enabled:** 12 | **Disabled:** 0

*Last generated: 2025-12-13T06:30:49Z*

| Module | Configured | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |
|--------|-----------|-----------|-------------------|--------------------|--------|
| analysis | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| audio | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| calibration | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| celery | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| detection | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| mlflow | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| observability | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| rate_limiting | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| risk_engine | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| sar | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| tenants | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |
| transcription | ✅ | ✅ | N/A | 2025-12-13T06:30:49Z | configured |

<!-- MODULE_STATUS_TABLE_END -->

## Integration Status (Incode)

| Component | Status | Verified |
|-----------|--------|----------|
| **Session API** | ✅ Active | Complete lifecycle |
| **Biometric Auth** | ✅ Active | Incode SDK wrapped |
| **Voice Auth** | ✅ Active | Sonotheia SDK wrapped |
| **Risk Fusion** | ✅ Active | Composite scoring |
| **Escalation** | ✅ Active | Human-in-the-loop |
| **Audit Logs** | ✅ Active | Compliance ready |

## Sensor Status (Patent Compliance)

| Sensor | Status | Compliance Method | Weight |
|--------|--------|-------------------|--------|
| **FormantTrajectory** | ✅ Active | Dynamic Velocity Analysis | 0.35 |
| **PhaseCoherence** | ✅ Active | Entropy & Discontinuity | 0.25 |
| **Coarticulation** | ✅ Active | Motor Planning (White Space) | 0.20 |
| **Bandwidth** | ✅ Active | Spectral Analysis | 0.10 |
| **BreathSensor** | ✅ Active | Phonation Duration (non-LPC) | 0.15 |
| **DynamicRange** | ✅ Active | Crest Factor Analysis | 0.10 |
| **GlottalInertia** | ✅ Active | Amplitude Rise Velocity | 0.15 |
| **GlobalFormant** | ✅ Active | Spectral Envelope Statistics | 0.10 |
| **DigitalSilence** | ✅ Active | Non-biological Silence Detection | 0.10 |
| **HuggingFace** | ⚠️ Optional | Transformer Model (requires huggingface_hub) | 0.10 |
| *VocalTract (LPC)* | ❌ Removed | Static LPC Analysis (Infringing) | 0.00 |

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Module is enabled and operational |
| ❌ | Module is disabled |

## Column Descriptions

- **Module**: Name of the platform module
- **Configured**: State defined in `modules.yaml` configuration
- **Effective**: Current runtime state (may differ from configured due to environment overrides)
- **Last Change (UTC)**: Timestamp of last effective state change
- **Last Recheck (UTC)**: Timestamp of last health check
- **Reason**: Why the module is in its current state

## How Status is Updated

The module status is automatically updated by the [ops-check workflow](.github/workflows/ops-check.yml) which runs:

1. **On Schedule**: Daily at 6:00 AM UTC
2. **On Push**: When changes are made to `modules.yaml`, backend code, or the workflow itself
3. **Manually**: Via workflow dispatch from the Actions tab

## Related Documentation

- [Module Control Documentation](README_MODULE_CONTROL.md) - Complete guide to module configuration
- [Configuration File](modules.yaml) - Module definitions and default states
- [API Documentation](Documentation/API.md) - REST API endpoints including admin module endpoints

## Manual Status Check

To manually check module status locally:

```bash
# Start services
./start.sh

# Generate status table
python scripts/generate_module_status_table.py --api-url http://localhost:8000

# Run operability verification
python scripts/ci_verify_operability.py --base-url http://localhost:8000
```
