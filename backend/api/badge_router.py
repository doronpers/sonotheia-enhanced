"""
FastAPI router providing Shields.io-compatible badge endpoints for module enablement ratios.
Adds 5s in-memory caching and explicit no-cache headers.
"""
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from core.module_registry import get_registry

router = APIRouter(tags=["badge"], prefix="/api/badge")

_cache = {"data": None, "expires": 0}

@router.get("/modules_enabled")
def modules_enabled_badge():
    """Return Shields.io schema showing enabled/total modules and color-coded ratio.
    Color thresholds:
      >=80% brightgreen
      >=50% yellow
      else red
    Lightgrey 'init' if registry not ready or empty.
    """
    now = time.time()
    if _cache["data"] and _cache["expires"] > now:
        resp = JSONResponse(content=_cache["data"])
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp

    try:
        registry = get_registry()
        modules = getattr(registry, "modules", []) or []
        total = len(modules)
        enabled = 0
        for m in modules:
            if isinstance(m, dict):
                eff = m.get("effective_enabled")
                if eff is None:
                    eff = m.get("enabled", False)
            else:
                eff = getattr(m, "effective_enabled", getattr(m, "enabled", False))
            if eff:
                enabled += 1
        if total == 0:
            data = {
                "schemaVersion": 1,
                "label": "modules",
                "message": "init",
                "color": "lightgrey"
            }
        else:
            ratio = enabled / total
            color = "brightgreen" if ratio >= 0.8 else ("yellow" if ratio >= 0.5 else "red")
            data = {
                "schemaVersion": 1,
                "label": "modules",
                "message": f"{enabled}/{total}",
                "color": color
            }
    except Exception:
        data = {
            "schemaVersion": 1,
            "label": "modules",
            "message": "init",
            "color": "lightgrey"
        }

    _cache["data"] = data
    _cache["expires"] = now + 5

    resp = JSONResponse(content=data)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp
