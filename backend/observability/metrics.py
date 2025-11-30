"""
Prometheus Metrics for Module Registry

Exports module state as Prometheus metrics:
- sonotheia_module_enabled{name="<module>"} 0|1

Usage:
    from observability.metrics import update_module_metrics, get_metrics_app

    # Update metrics when module states change
    update_module_metrics()

    # Mount metrics endpoint in FastAPI
    app.mount("/metrics", get_metrics_app())
"""

import logging
from typing import Dict, Optional
from prometheus_client import Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Create a dedicated registry to avoid conflicts with default registry
REGISTRY = CollectorRegistry()

# Module state gauge: 1 = enabled, 0 = disabled
MODULE_ENABLED_GAUGE = Gauge(
    "sonotheia_module_enabled",
    "Whether a Sonotheia module is enabled (1) or disabled (0)",
    ["name"],
    registry=REGISTRY,
)

# Track last known states to avoid redundant updates
_last_known_states: Dict[str, bool] = {}


def update_module_metrics(module_states: Optional[Dict[str, bool]] = None) -> None:
    """
    Update Prometheus metrics based on current module states.

    Args:
        module_states: Optional dict of module_name -> enabled state.
                      If None, fetches from registry.
    """
    global _last_known_states

    if module_states is None:
        # Import here to avoid circular imports
        from core.module_registry import get_registry

        registry = get_registry()
        modules = registry.list_modules()
        module_states = {
            name: info.get("enabled", True) for name, info in modules.items()
        }

    for module_name, enabled in module_states.items():
        value = 1 if enabled else 0
        MODULE_ENABLED_GAUGE.labels(name=module_name).set(value)
        _last_known_states[module_name] = enabled

    logger.debug(f"Updated metrics for {len(module_states)} modules")


def get_module_metrics_values() -> Dict[str, int]:
    """
    Get current metrics values for all modules.

    Returns:
        Dictionary of module_name -> metric value (0 or 1)
    """
    return {name: (1 if enabled else 0) for name, enabled in _last_known_states.items()}


def refresh_metrics() -> Dict[str, int]:
    """
    Force refresh of all module metrics from current registry state.

    Returns:
        Dictionary of updated module metrics values.
    """
    update_module_metrics()
    return get_module_metrics_values()


async def metrics_endpoint(request: Request) -> Response:
    """
    FastAPI/Starlette endpoint handler for /metrics.

    Returns Prometheus metrics in text format.
    """
    # Refresh metrics before serving
    update_module_metrics()

    metrics_output = generate_latest(REGISTRY)
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST,
    )


def get_metrics_route():
    """
    Get a route handler for mounting metrics endpoint.

    Usage in FastAPI:
        from observability.metrics import get_metrics_route
        app.add_api_route("/metrics", get_metrics_route(), methods=["GET"])

    Returns:
        Async function to handle metrics requests.
    """
    return metrics_endpoint
