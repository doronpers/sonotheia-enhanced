# Sonotheia Enhanced - System Status

> Live operational status of Sonotheia Enhanced platform modules and services

[![Ops Check](https://github.com/doronpers/sonotheia-enhanced/actions/workflows/ops-check.yml/badge.svg)](https://github.com/doronpers/sonotheia-enhanced/actions/workflows/ops-check.yml)

## Overview

This document provides the current operational status of all platform modules. The status table below is automatically updated by the CI/CD pipeline when changes are made to the module configuration or backend services.

<!-- MODULE_STATUS_TABLE_START -->

## Module Status

**Profile:** standard | **Total:** 3 | **Enabled:** 2 | **Disabled:** 1

*Last generated: (auto-updated by CI)*

| Module | Configured | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |
|--------|-----------|-----------|-------------------|--------------------|--------|
| audio | ✅ | ✅ | N/A | N/A | configured |
| detection | ✅ | ✅ | N/A | N/A | configured |
| calibration | ❌ | ❌ | N/A | N/A | configured |

<!-- MODULE_STATUS_TABLE_END -->

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
