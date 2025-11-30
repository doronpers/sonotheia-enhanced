"""
Admin Module Routes

API endpoints for listing and toggling module states.
These endpoints require admin-level authentication.
"""

import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field, ConfigDict

# Note: sys.path modification is used to match existing codebase patterns
# (see analyze_call.py, session_management.py, etc.)
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.module_registry import get_registry  # noqa: E402
from core.profiles import list_profiles  # noqa: E402
from api.middleware import limiter, verify_api_key, get_error_response  # noqa: E402
from observability.metrics import refresh_metrics, get_module_metrics_values  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/modules", tags=["admin"])


class ModuleInfo(BaseModel):
    """Module information response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "calibration",
                "configured_enabled": True,
                "effective_enabled": True,
                "description": "Audio calibration and preprocessing tools",
                "metrics_value": 1,
                "last_effective_change": "2025-01-15T10:30:00Z",
                "reason": "configured",
            }
        }
    )

    name: str = Field(..., description="Module name")
    enabled: bool = Field(..., description="Whether the module is currently enabled (effective)")
    configured_enabled: Optional[bool] = Field(
        None, description="Whether the module is enabled in configuration"
    )
    effective_enabled: Optional[bool] = Field(
        None, description="Whether the module is currently enabled (runtime)"
    )
    description: Optional[str] = Field(None, description="Module description")
    metrics_value: Optional[int] = Field(
        None, description="Prometheus metrics value (0 or 1)"
    )
    last_effective_change: Optional[str] = Field(
        None, description="ISO8601 timestamp of last effective state change"
    )
    reason: Optional[str] = Field(
        None, description="Reason for effective state: configured, runtime_enabled, runtime_disabled"
    )


class ModuleListResponse(BaseModel):
    """Response containing list of all modules."""

    modules: List[ModuleInfo] = Field(..., description="List of all modules")
    total: int = Field(..., description="Total number of modules")
    enabled_count: int = Field(..., description="Number of enabled modules")
    disabled_count: int = Field(..., description="Number of disabled modules")
    profile: str = Field(..., description="Current module profile")
    available_profiles: Dict[str, Dict] = Field(
        ..., description="Available profile presets"
    )
    last_health_recheck: Optional[str] = Field(
        None, description="ISO8601 timestamp of last health recheck"
    )


class ModuleToggleRequest(BaseModel):
    """Request to toggle module state."""

    model_config = ConfigDict(json_schema_extra={"example": {"enabled": False}})

    enabled: bool = Field(..., description="New enabled state for the module")


class ModuleToggleResponse(BaseModel):
    """Response after toggling module state."""

    module: str = Field(..., description="Module name")
    enabled: bool = Field(..., description="New enabled state")
    previous_state: bool = Field(..., description="Previous enabled state")
    message: str = Field(..., description="Status message")


class RecheckResponse(BaseModel):
    """Response from health recheck endpoint."""

    message: str = Field(..., description="Status message")
    modules_updated: int = Field(..., description="Number of modules updated")
    metrics: Dict[str, int] = Field(..., description="Updated metrics values")
    last_health_recheck: Optional[str] = Field(
        None, description="ISO8601 timestamp of this health recheck"
    )


class ModuleSummaryResponse(BaseModel):
    """Summary of module states for quick overview."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 12,
                "enabled": 10,
                "disabled": 2,
                "last_recheck": "2025-01-15T10:30:00Z",
            }
        }
    )

    total: int = Field(..., description="Total number of modules")
    enabled: int = Field(..., description="Number of enabled modules")
    disabled: int = Field(..., description="Number of disabled modules")
    last_recheck: Optional[str] = Field(
        None, description="ISO8601 timestamp of last health recheck"
    )


def _is_admin_tier(api_key_info: dict) -> bool:
    """
    Check if the API key has admin privileges.

    In production, implement proper role-based access control.
    For demo mode, 'premium' tier is treated as admin.
    """
    tier = api_key_info.get("tier", "free")
    return tier in ("admin", "premium")


async def require_admin(
    request: Request, api_key_info: dict = Depends(verify_api_key)
) -> dict:
    """
    Dependency that requires admin-level access.

    Raises HTTPException 403 if user doesn't have admin privileges.
    """
    if not _is_admin_tier(api_key_info):
        logger.warning(
            f"Non-admin access attempt to admin endpoint "
            f"from client '{api_key_info.get('client', 'unknown')}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_error_response(
                "FORBIDDEN", "Admin privileges required for this endpoint"
            ),
        )
    return api_key_info


@router.get(
    "",
    response_model=ModuleListResponse,
    summary="List All Modules",
    description="Get a list of all modules and their current states",
)
@limiter.limit("100/minute")
async def list_modules(request: Request, admin_info: dict = Depends(require_admin)):
    """
    List all modules and their enabled/disabled states.

    **Requires**: Admin-level API key

    **Rate Limit**: 100 requests per minute

    **Returns**: List of all modules with their states, profile info, and metrics
    """
    registry = get_registry()
    modules_with_ts = registry.list_modules_with_timestamps()

    # Get current metrics values
    metrics_values = get_module_metrics_values()

    modules = []
    for mod_info in modules_with_ts:
        modules.append(
            ModuleInfo(
                name=mod_info["name"],
                enabled=mod_info["effective_enabled"],
                configured_enabled=mod_info["configured_enabled"],
                effective_enabled=mod_info["effective_enabled"],
                description=mod_info["description"],
                metrics_value=metrics_values.get(mod_info["name"]),
                last_effective_change=mod_info["last_effective_change"],
                reason=mod_info["reason"],
            )
        )

    enabled_count = len([m for m in modules if m.enabled])
    disabled_count = len(modules) - enabled_count

    logger.info(
        f"Admin '{admin_info.get('client', 'unknown')}' listed modules: "
        f"{len(modules)} total, {enabled_count} enabled, {disabled_count} disabled"
    )

    return ModuleListResponse(
        modules=modules,
        total=len(modules),
        enabled_count=enabled_count,
        disabled_count=disabled_count,
        profile=registry.get_profile(),
        available_profiles=list_profiles(),
        last_health_recheck=registry.get_last_health_recheck(),
    )


@router.get(
    "/summary",
    response_model=ModuleSummaryResponse,
    summary="Module Summary",
    description="Get a quick summary of module states",
)
@limiter.limit("100/minute")
async def get_modules_summary(
    request: Request, admin_info: dict = Depends(require_admin)
):
    """
    Get a summary of module states.

    **Requires**: Admin-level API key

    **Rate Limit**: 100 requests per minute

    **Returns**: Total, enabled, and disabled counts with last recheck timestamp
    """
    registry = get_registry()
    modules = registry.list_modules()

    total = len(modules)
    enabled = len([m for m in modules.values() if m.get("enabled", True)])
    disabled = total - enabled

    logger.debug(
        f"Module summary requested: {total} total, {enabled} enabled, {disabled} disabled"
    )

    return ModuleSummaryResponse(
        total=total,
        enabled=enabled,
        disabled=disabled,
        last_recheck=registry.get_last_health_recheck(),
    )


@router.post(
    "/recheck",
    response_model=RecheckResponse,
    summary="Recheck Module Health",
    description="Force a health re-assessment and refresh metrics for all modules",
)
@limiter.limit("10/minute")
async def recheck_modules(
    request: Request, admin_info: dict = Depends(require_admin)
):
    """
    Force a health re-assessment and refresh Prometheus metrics.

    **Requires**: Admin-level API key

    **Rate Limit**: 10 requests per minute

    **Returns**: Updated metrics for all modules
    """
    registry = get_registry()
    modules = registry.list_modules()

    # Update health recheck timestamp
    recheck_time = registry.update_health_recheck()

    # Refresh metrics based on current module states
    updated_metrics = refresh_metrics()

    logger.info(
        f"Admin '{admin_info.get('client', 'unknown')}' triggered module health recheck"
    )

    return RecheckResponse(
        message="Module health recheck completed and metrics refreshed",
        modules_updated=len(modules),
        metrics=updated_metrics,
        last_health_recheck=recheck_time,
    )


@router.get(
    "/{module_name}",
    response_model=ModuleInfo,
    summary="Get Module Info",
    description="Get information about a specific module",
)
@limiter.limit("100/minute")
async def get_module(
    request: Request, module_name: str, admin_info: dict = Depends(require_admin)
):
    """
    Get information about a specific module.

    **Requires**: Admin-level API key

    **Rate Limit**: 100 requests per minute

    **Parameters**:
    - `module_name`: Name of the module to query

    **Returns**: Module information including enabled state
    """
    registry = get_registry()
    mod_info = registry.get_module_with_timestamps(module_name)

    if mod_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Module '{module_name}' not found"),
        )

    # Get metrics value
    metrics_values = get_module_metrics_values()

    return ModuleInfo(
        name=mod_info["name"],
        enabled=mod_info["effective_enabled"],
        configured_enabled=mod_info["configured_enabled"],
        effective_enabled=mod_info["effective_enabled"],
        description=mod_info["description"],
        metrics_value=metrics_values.get(mod_info["name"]),
        last_effective_change=mod_info["last_effective_change"],
        reason=mod_info["reason"],
    )


@router.put(
    "/{module_name}",
    response_model=ModuleToggleResponse,
    summary="Toggle Module State",
    description="Enable or disable a module at runtime",
)
@limiter.limit("20/minute")
async def toggle_module(
    request: Request,
    module_name: str,
    toggle_request: ModuleToggleRequest,
    admin_info: dict = Depends(require_admin),
):
    """
    Enable or disable a module at runtime.

    **Requires**: Admin-level API key

    **Rate Limit**: 20 requests per minute (protective limit for state changes)

    **Parameters**:
    - `module_name`: Name of the module to toggle

    **Body**:
    - `enabled`: New enabled state (true/false)

    **Returns**: Updated module state

    **Note**: Changes only affect runtime state and will reset on restart.
    For persistent changes, update modules.yaml or use environment variables.
    """
    registry = get_registry()

    # Get previous state
    info = registry.get_module_info(module_name)
    if info is None:
        previous_state = True  # Default for unknown modules
    else:
        previous_state = info.get("enabled", True)

    # Apply the change
    registry.set_enabled(module_name, toggle_request.enabled)

    action = "enabled" if toggle_request.enabled else "disabled"
    logger.info(
        f"Admin '{admin_info.get('client', 'unknown')}' {action} module '{module_name}' "
        f"(previous state: {previous_state})"
    )

    return ModuleToggleResponse(
        module=module_name,
        enabled=toggle_request.enabled,
        previous_state=previous_state,
        message=f"Module '{module_name}' has been {action}",
    )


@router.post(
    "/{module_name}/enable",
    response_model=ModuleToggleResponse,
    summary="Enable Module",
    description="Enable a module (convenience endpoint)",
)
@limiter.limit("20/minute")
async def enable_module(
    request: Request, module_name: str, admin_info: dict = Depends(require_admin)
):
    """
    Enable a specific module.

    **Requires**: Admin-level API key

    **Rate Limit**: 20 requests per minute

    **Parameters**:
    - `module_name`: Name of the module to enable

    **Returns**: Updated module state
    """
    registry = get_registry()

    info = registry.get_module_info(module_name)
    previous_state = info.get("enabled", True) if info else True

    registry.set_enabled(module_name, True)

    logger.info(
        f"Admin '{admin_info.get('client', 'unknown')}' enabled module '{module_name}'"
    )

    return ModuleToggleResponse(
        module=module_name,
        enabled=True,
        previous_state=previous_state,
        message=f"Module '{module_name}' has been enabled",
    )


@router.post(
    "/{module_name}/disable",
    response_model=ModuleToggleResponse,
    summary="Disable Module",
    description="Disable a module (convenience endpoint)",
)
@limiter.limit("20/minute")
async def disable_module(
    request: Request, module_name: str, admin_info: dict = Depends(require_admin)
):
    """
    Disable a specific module.

    **Requires**: Admin-level API key

    **Rate Limit**: 20 requests per minute

    **Parameters**:
    - `module_name`: Name of the module to disable

    **Returns**: Updated module state
    """
    registry = get_registry()

    info = registry.get_module_info(module_name)
    previous_state = info.get("enabled", True) if info else True

    registry.set_enabled(module_name, False)

    logger.info(
        f"Admin '{admin_info.get('client', 'unknown')}' disabled module '{module_name}'"
    )

    return ModuleToggleResponse(
        module=module_name,
        enabled=False,
        previous_state=previous_state,
        message=f"Module '{module_name}' has been disabled",
    )
