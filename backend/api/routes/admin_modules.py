"""
Admin Module Routes

API endpoints for listing and toggling module states.
These endpoints require admin-level authentication.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field, ConfigDict

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.module_registry import get_registry  # noqa: E402
from api.middleware import limiter, verify_api_key, get_error_response  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/modules", tags=["admin"])


class ModuleInfo(BaseModel):
    """Module information response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "calibration",
                "enabled": True,
                "description": "Audio calibration and preprocessing tools",
            }
        }
    )

    name: str = Field(..., description="Module name")
    enabled: bool = Field(..., description="Whether the module is currently enabled")
    description: Optional[str] = Field(None, description="Module description")


class ModuleListResponse(BaseModel):
    """Response containing list of all modules."""

    modules: List[ModuleInfo] = Field(..., description="List of all modules")
    total: int = Field(..., description="Total number of modules")
    enabled_count: int = Field(..., description="Number of enabled modules")
    disabled_count: int = Field(..., description="Number of disabled modules")


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

    **Returns**: List of all modules with their states
    """
    registry = get_registry()
    modules_dict = registry.list_modules()

    modules = []
    for name, info in modules_dict.items():
        modules.append(
            ModuleInfo(
                name=name,
                enabled=info.get("enabled", True),
                description=info.get("description"),
            )
        )

    # Sort modules alphabetically by name
    modules.sort(key=lambda m: m.name)

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
    info = registry.get_module_info(module_name)

    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Module '{module_name}' not found"),
        )

    return ModuleInfo(
        name=module_name,
        enabled=info.get("enabled", True),
        description=info.get("description"),
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
