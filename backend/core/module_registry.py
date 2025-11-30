"""
Module Registry

Centralized module management for enabling/disabling features at runtime.

Configuration loading order (later overrides earlier):
1. Profile defaults (MODULE_PROFILE=minimal|standard|full)
2. YAML configuration (modules.yaml)
3. Environment variable overrides (MODULE_<NAME>=0|1)
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Set
import yaml

from core.profiles import get_current_profile, get_profile_defaults

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    """Return current UTC time in ISO8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ModuleRegistry:
    """
    Centralized registry for managing module states.

    Configuration loading order (later overrides earlier):
    1. Profile defaults (from MODULE_PROFILE env var)
    2. YAML configuration (modules.yaml)
    3. Environment variable overrides (MODULE_<NAME>=0|1)
    """

    _instance: Optional["ModuleRegistry"] = None

    def __new__(cls, config_path: Optional[str] = None) -> "ModuleRegistry":
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._modules = {}
            cls._instance._config_path = None
            cls._instance._profile = None
            cls._instance._configured_modules = {}  # Before health gating
            cls._instance._last_health_recheck = None  # Global last recheck timestamp
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the module registry.

        Args:
            config_path: Optional path to modules.yaml file.
                        Defaults to <repo_root>/modules.yaml
        """
        # Only initialize once (singleton pattern)
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self._modules = {}
        self._configured_modules = {}
        self._last_health_recheck = _utc_now()  # Initialize on startup

        # Determine config path
        if config_path:
            self._config_path = Path(config_path)
        else:
            # Default: look for modules.yaml at repo root
            # Walk up from this file to find repo root
            current = Path(__file__).parent.parent.parent
            self._config_path = current / "modules.yaml"

        # Load configuration in order: profile -> YAML -> env
        self._profile = get_current_profile()
        self._apply_profile_defaults()
        self._load_yaml_config()
        self._apply_env_overrides()

        # Store configured state before any health gating
        self._configured_modules = {
            name: info.copy() for name, info in self._modules.items()
        }

        logger.info(
            f"ModuleRegistry initialized with profile '{self._profile}' "
            f"and {len(self._modules)} modules"
        )

    def _apply_profile_defaults(self) -> None:
        """Apply profile defaults as the base configuration."""
        profile_defaults = get_profile_defaults(self._profile)
        self._modules = profile_defaults
        logger.info(f"Applied profile '{self._profile}' defaults")

    def _load_yaml_config(self) -> None:
        """Load and merge YAML configuration (overrides profile defaults)."""
        if not self._config_path or not self._config_path.exists():
            logger.warning(
                f"Module config not found at {self._config_path}, using profile defaults"
            )
            return

        try:
            with open(self._config_path, "r") as f:
                config = yaml.safe_load(f)

            if isinstance(config, dict) and config.get("modules"):

                # Merge YAML config over profile defaults
                for name, info in config["modules"].items():
                    if info is None:
                        continue
                    # Validate info is a dictionary before merging
                    if not isinstance(info, dict):
                        logger.warning(
                            f"Invalid config for module '{name}': expected dict, got {type(info).__name__}"
                        )
                        continue
                    name_lower = name.lower()
                    if name_lower in self._modules:
                        self._modules[name_lower].update(info)
                    else:
                        self._modules[name_lower] = info
                logger.info(f"Merged YAML config from {self._config_path}")
            else:
                logger.warning(f"No 'modules' key found in {self._config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing modules.yaml: {e}")
        except IOError as e:
            logger.error(f"Error reading modules.yaml: {e}")

    def _apply_env_overrides(self) -> None:
        """
        Apply environment variable overrides to module states.

        Environment variables follow the pattern: MODULE_<NAME>=0|1
        Examples:
            MODULE_CALIBRATION=0  -> Disable calibration module
            MODULE_SAR=1          -> Enable SAR module

        Note: MODULE_PROFILE is handled separately and skipped here.
        """
        for key, value in os.environ.items():
            if key.startswith("MODULE_"):
                # Skip MODULE_PROFILE as it's handled separately
                if key == "MODULE_PROFILE":
                    continue

                module_name = key[7:].lower()  # Remove 'MODULE_' prefix

                # Parse boolean value
                if value in ("0", "false", "False", "FALSE", "no", "No", "NO"):
                    enabled = False
                elif value in ("1", "true", "True", "TRUE", "yes", "Yes", "YES"):
                    enabled = True
                else:
                    logger.warning(f"Invalid value '{value}' for {key}, ignoring")
                    continue

                # Update or create module entry
                if module_name in self._modules:
                    old_value = self._modules[module_name].get("enabled", True)
                    self._modules[module_name]["enabled"] = enabled
                    logger.info(
                        f"Env override: {module_name} enabled={enabled} (was {old_value})"
                    )
                else:
                    # Create new module entry from env var
                    self._modules[module_name] = {
                        "enabled": enabled,
                        "description": f"Module configured via {key}",
                    }
                    logger.info(f"Env created: {module_name} enabled={enabled}")

    def is_enabled(self, module_name: str) -> bool:
        """
        Check if a module is enabled.

        Args:
            module_name: Name of the module to check

        Returns:
            True if module is enabled, False otherwise.
            Returns True for unknown modules (safe default).
        """
        module = self._modules.get(module_name.lower())
        if module is None:
            logger.debug(f"Module '{module_name}' not found, defaulting to enabled")
            return True
        return module.get("enabled", True)

    def get_module_info(self, module_name: str) -> Optional[Dict]:
        """
        Get detailed information about a module.

        Args:
            module_name: Name of the module

        Returns:
            Module info dict or None if not found
        """
        return self._modules.get(module_name.lower())

    def list_modules(self) -> Dict[str, Dict]:
        """
        Get a copy of all modules and their states.

        Returns:
            Dictionary of module name -> module info
        """
        return dict(self._modules)

    def list_enabled(self) -> Set[str]:
        """
        Get set of all enabled module names.

        Returns:
            Set of enabled module names
        """
        return {
            name for name, info in self._modules.items() if info.get("enabled", True)
        }

    def list_disabled(self) -> Set[str]:
        """
        Get set of all disabled module names.

        Returns:
            Set of disabled module names
        """
        return {
            name
            for name, info in self._modules.items()
            if not info.get("enabled", True)
        }

    def set_enabled(self, module_name: str, enabled: bool) -> bool:
        """
        Set the enabled state of a module at runtime.

        Note: This only affects runtime state, not the YAML file.

        Args:
            module_name: Name of the module
            enabled: New enabled state

        Returns:
            True if module was found and updated, False otherwise
        """
        module_key = module_name.lower()
        now = _utc_now()
        if module_key in self._modules:
            old_value = self._modules[module_key].get("enabled", True)
            self._modules[module_key]["enabled"] = enabled
            # Update last_effective_change if effective state changed
            if old_value != enabled:
                self._modules[module_key]["last_effective_change"] = now
            logger.info(
                f"Module '{module_name}' set enabled={enabled} (was {old_value})"
            )
            return True

        # Create new module entry if it doesn't exist
        self._modules[module_key] = {
            "enabled": enabled,
            "description": f"Runtime-created module '{module_name}'",
            "last_effective_change": now,
        }
        logger.info(f"Module '{module_name}' created with enabled={enabled}")
        return True

    def get_profile(self) -> str:
        """
        Get the current profile name.

        Returns:
            Profile name (minimal, standard, or full)
        """
        return self._profile

    def get_configured_modules(self) -> Dict[str, Dict]:
        """
        Get modules as configured (before any health gating).

        Returns:
            Dictionary of configured module states
        """
        return dict(self._configured_modules)

    def get_effective_modules(self) -> Dict[str, Dict]:
        """
        Get modules with their effective (current) states.

        This reflects any runtime changes including health gating.

        Returns:
            Dictionary of effective module states
        """
        return dict(self._modules)

    def get_last_health_recheck(self) -> Optional[str]:
        """
        Get the timestamp of the last health recheck.

        Returns:
            ISO8601 UTC timestamp string or None if never rechecked
        """
        return self._last_health_recheck

    def update_health_recheck(self) -> str:
        """
        Update the global last health recheck timestamp.

        Returns:
            The new timestamp in ISO8601 UTC format
        """
        self._last_health_recheck = _utc_now()
        logger.debug(f"Health recheck timestamp updated: {self._last_health_recheck}")
        return self._last_health_recheck

    def get_module_with_timestamps(self, module_name: str) -> Optional[Dict]:
        """
        Get detailed module info including timestamps.

        Args:
            module_name: Name of the module

        Returns:
            Module info dict with configured_enabled, effective_enabled,
            last_effective_change, and reason, or None if not found
        """
        module_key = module_name.lower()
        if module_key not in self._modules:
            return None

        effective = self._modules[module_key]
        configured = self._configured_modules.get(module_key, {})

        configured_enabled = configured.get("enabled", True)
        effective_enabled = effective.get("enabled", True)

        # Determine reason for state
        if configured_enabled == effective_enabled:
            reason = "configured"
        elif effective_enabled:
            reason = "runtime_enabled"
        else:
            reason = "runtime_disabled"

        return {
            "name": module_key,
            "configured_enabled": configured_enabled,
            "effective_enabled": effective_enabled,
            "description": effective.get("description", ""),
            "last_effective_change": effective.get("last_effective_change"),
            "reason": reason,
        }

    def list_modules_with_timestamps(self) -> list:
        """
        Get all modules with their configured/effective states and timestamps.

        Returns:
            List of module info dicts with timestamps
        """
        result = []
        for module_name in sorted(self._modules.keys()):
            info = self.get_module_with_timestamps(module_name)
            if info:
                result.append(info)
        return result

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance. Useful for testing.
        """
        cls._instance = None


# Create a module-level convenience function
def get_registry(config_path: Optional[str] = None) -> ModuleRegistry:
    """
    Get the module registry instance.

    Args:
        config_path: Optional path to modules.yaml (only used on first call)

    Returns:
        ModuleRegistry singleton instance
    """
    return ModuleRegistry(config_path)


def is_module_enabled(module_name: str) -> bool:
    """
    Check if a module is enabled.

    Convenience function that uses the default registry.

    Args:
        module_name: Name of the module to check

    Returns:
        True if module is enabled
    """
    return get_registry().is_enabled(module_name)
