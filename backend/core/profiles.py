"""
Module Profile Presets

Provides predefined module sets for different deployment environments.
Profile selection order: MODULE_PROFILE env -> full (default)
Configuration order: profile defaults -> YAML overrides -> env overrides
"""

import os
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

# Profile preset definitions
PROFILE_PRESETS: Dict[str, Set[str]] = {
    "minimal": {
        "audio",
        "detection",
        "sar",
        "rate_limiting",
        "observability",
    },
    "standard": {
        # Includes all minimal modules
        "audio",
        "detection",
        "sar",
        "rate_limiting",
        "observability",
        # Plus additional modules
        "calibration",
        "analysis",
        "celery",
    },
    "full": {
        # Includes all standard modules
        "audio",
        "detection",
        "sar",
        "rate_limiting",
        "observability",
        "calibration",
        "analysis",
        "celery",
        # Plus advanced modules
        "transcription",
        "tenants",
        "mlflow",
        "risk_engine",
    },
}

# Default profile when MODULE_PROFILE is not set
DEFAULT_PROFILE = "full"


def get_current_profile() -> str:
    """
    Get the current profile from environment variable.

    Returns:
        Profile name (minimal, standard, or full). Defaults to 'full'.
    """
    profile = os.environ.get("MODULE_PROFILE", DEFAULT_PROFILE).lower()

    if profile not in PROFILE_PRESETS:
        logger.warning(
            f"Unknown profile '{profile}', falling back to '{DEFAULT_PROFILE}'"
        )
        return DEFAULT_PROFILE

    return profile


def get_profile_modules(profile_name: str = None) -> Set[str]:
    """
    Get the set of enabled modules for a given profile.

    Args:
        profile_name: Name of the profile. If None, uses current profile from env.

    Returns:
        Set of module names enabled in the profile.
    """
    if profile_name is None:
        profile_name = get_current_profile()

    profile_name = profile_name.lower()

    if profile_name not in PROFILE_PRESETS:
        logger.warning(
            f"Unknown profile '{profile_name}', using '{DEFAULT_PROFILE}'"
        )
        profile_name = DEFAULT_PROFILE

    return PROFILE_PRESETS[profile_name].copy()


def get_profile_defaults(profile_name: str = None) -> Dict[str, Dict]:
    """
    Get module configuration defaults based on profile.

    Modules in the profile are enabled by default, others are disabled.

    Args:
        profile_name: Name of the profile. If None, uses current profile from env.

    Returns:
        Dictionary of module configurations with enabled states.
    """
    enabled_modules = get_profile_modules(profile_name)

    # Get all known modules from the full profile
    all_modules = PROFILE_PRESETS["full"]

    defaults = {}
    for module in all_modules:
        defaults[module] = {
            "enabled": module in enabled_modules,
            "description": f"Module '{module}' (profile default)",
        }

    return defaults


def list_profiles() -> Dict[str, Dict]:
    """
    List all available profiles with their module counts.

    Returns:
        Dictionary with profile names and their metadata.
    """
    return {
        name: {
            "modules": sorted(modules),
            "module_count": len(modules),
        }
        for name, modules in PROFILE_PRESETS.items()
    }
