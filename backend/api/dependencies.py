"""
API Dependencies

FastAPI dependency injection components for common functionality
including module availability guards.
"""

import logging
from typing import Callable
from fastapi import Request, HTTPException, status

# Import from sibling packages
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.module_registry import get_registry  # noqa: E402

logger = logging.getLogger(__name__)


class ModuleDisabledException(HTTPException):
    """Exception raised when accessing a disabled module."""

    def __init__(self, module_name: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "MODULE_DISABLED",
                "message": f"Module '{module_name}' is currently disabled",
                "module": module_name,
            },
        )


def require_module(module_name: str) -> Callable:
    """
    FastAPI dependency that ensures a module is enabled.

    Usage:
        @app.get("/api/calibration/status")
        async def calibration_status(
            _: None = Depends(require_module("calibration"))
        ):
            ...

    Args:
        module_name: Name of the required module

    Returns:
        Dependency callable that raises HTTP 503 if module is disabled

    Raises:
        HTTPException: 503 Service Unavailable if module is disabled
    """

    async def dependency(request: Request) -> None:
        registry = get_registry()
        if not registry.is_enabled(module_name):
            logger.warning(
                f"Access denied to disabled module '{module_name}' "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            raise ModuleDisabledException(module_name)
        return None

    return dependency


def require_any_module(*module_names: str) -> Callable:
    """
    FastAPI dependency that ensures at least one of the specified modules is enabled.

    Usage:
        @app.get("/api/feature")
        async def feature(
            _: None = Depends(require_any_module("module_a", "module_b"))
        ):
            ...

    Args:
        module_names: Names of modules to check (any one being enabled is sufficient)

    Returns:
        Dependency callable that raises HTTP 503 if all modules are disabled
    """

    async def dependency(request: Request) -> None:
        registry = get_registry()
        for module_name in module_names:
            if registry.is_enabled(module_name):
                return None

        logger.warning(
            f"Access denied - all modules disabled: {module_names} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "MODULES_DISABLED",
                "message": f"None of the required modules are enabled: {', '.join(module_names)}",
                "modules": list(module_names),
            },
        )

    return dependency


def require_all_modules(*module_names: str) -> Callable:
    """
    FastAPI dependency that ensures all specified modules are enabled.

    Usage:
        @app.get("/api/feature")
        async def feature(
            _: None = Depends(require_all_modules("module_a", "module_b"))
        ):
            ...

    Args:
        module_names: Names of modules that must all be enabled

    Returns:
        Dependency callable that raises HTTP 503 if any module is disabled
    """

    async def dependency(request: Request) -> None:
        registry = get_registry()
        disabled = [name for name in module_names if not registry.is_enabled(name)]

        if disabled:
            logger.warning(
                f"Access denied - modules disabled: {disabled} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error_code": "MODULES_DISABLED",
                    "message": f"Required modules are disabled: {', '.join(disabled)}",
                    "disabled_modules": disabled,
                    "required_modules": list(module_names),
                },
            )
        return None

    return dependency
