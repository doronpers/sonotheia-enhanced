"""
FastAPI router providing Shields.io-compatible badge endpoints for module enablement ratios.
"""
from fastapi import APIRouter
from core.module_registry import get_registry

router = APIRouter(tags=["metrics"], prefix="/api/badge")

@router.get("/modules_enabled")
def modules_enabled_badge():
    """Return Shields.io schema showing enabled/total modules and color-coded ratio."""
    try:
        registry = get_registry()
        modules = getattr(registry, "modules", []) or []
        total = len(modules)
        enabled = 0
        for m in modules:
            # Support both object and dict forms
            if isinstance(m, dict):
                effective = m.get("effective_enabled")
                if effective is None:
                    effective = m.get("enabled", False)
            else:
                effective = getattr(m, "effective_enabled", None)
                if effective is None:
                    effective = getattr(m, "enabled", False)
            if effective:
                enabled += 1
        ratio = enabled / total if total else 0.0
        color = "brightgreen" if ratio >= 0.8 else ("yellow" if ratio >= 0.5 else "red")
        return {
            "schemaVersion": 1,
            "label": "modules",
            "message": f"{enabled}/{total}",
            "color": color
        }
    except Exception:
        # Fallback for initialization race conditions
        return {
            "schemaVersion": 1,
            "label": "modules",
            "message": "init",
            "color": "lightgrey"
        }