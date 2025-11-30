"""
Badge Routes

Public endpoints for Shields.io dynamic badges.
These endpoints are lightweight and do not require authentication.
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, ConfigDict

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.module_registry import get_registry  # noqa: E402
from api.middleware import limiter  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/badge", tags=["badge"])

# Simple in-memory cache for badge responses with thread-safe lock
import threading

_badge_cache_lock = threading.Lock()
_badge_cache = {
    "modules_enabled": None,
    "cache_time": 0.0,
}
_CACHE_TTL_SECONDS = 5.0


class ShieldsBadgeResponse(BaseModel):
    """Shields.io endpoint badge schema."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schemaVersion": 1,
                "label": "modules",
                "message": "10/12",
                "color": "brightgreen",
            }
        }
    )

    schemaVersion: int = Field(1, description="Shields.io schema version")
    label: str = Field(..., description="Badge label")
    message: str = Field(..., description="Badge message/value")
    color: str = Field(..., description="Badge color: brightgreen, yellow, red, etc.")


def _get_badge_color(enabled: int, total: int) -> str:
    """
    Determine badge color based on enabled ratio.

    Thresholds:
    - >=80% enabled: brightgreen
    - >=50% enabled: yellow
    - <50% enabled: red

    Args:
        enabled: Number of enabled modules
        total: Total number of modules

    Returns:
        Color string for Shields.io badge
    """
    if total == 0:
        return "lightgrey"

    ratio = enabled / total

    if ratio >= 0.80:
        return "brightgreen"
    elif ratio >= 0.50:
        return "yellow"
    else:
        return "red"


@router.get(
    "/modules_enabled",
    response_model=ShieldsBadgeResponse,
    summary="Modules Enabled Badge",
    description="Shields.io endpoint for dynamic modules enabled badge",
)
@limiter.limit("200/minute")
async def modules_enabled_badge(request: Request):
    """
    Get Shields.io badge data for enabled modules.

    This endpoint returns a Shields.io compatible JSON response
    showing the number of enabled modules vs total modules.

    **Rate Limit**: 200 requests per minute (lightweight endpoint)

    **Returns**: Shields.io badge schema with enabled/total count

    **Color thresholds**:
    - >=80% enabled: brightgreen
    - >=50% enabled: yellow
    - <50% enabled: red

    **Usage**:
    ```
    https://img.shields.io/endpoint?url=<BASE_URL>/api/badge/modules_enabled
    ```
    """
    global _badge_cache

    current_time = time.time()

    # Thread-safe cache read
    with _badge_cache_lock:
        if (
            _badge_cache["modules_enabled"] is not None
            and (current_time - _badge_cache["cache_time"]) < _CACHE_TTL_SECONDS
        ):
            logger.debug("Returning cached badge response")
            return _badge_cache["modules_enabled"]

    # Compute fresh response (outside lock for better concurrency)
    registry = get_registry()
    modules = registry.list_modules()

    total = len(modules)
    enabled = len([m for m in modules.values() if m.get("enabled", True)])

    color = _get_badge_color(enabled, total)
    message = f"{enabled}/{total}"

    response = ShieldsBadgeResponse(
        schemaVersion=1,
        label="modules",
        message=message,
        color=color,
    )

    # Thread-safe cache update
    with _badge_cache_lock:
        _badge_cache["modules_enabled"] = response
        _badge_cache["cache_time"] = current_time

    logger.debug(f"Badge response: {message} ({color})")
    return response
