"""
Module Registry

Centralized module management for enabling/disabling features at runtime.
Loads configuration from modules.yaml and allows environment variable overrides.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Set
import yaml

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Centralized registry for managing module states.

    Loads module configuration from YAML file and supports environment
    variable overrides (e.g., MODULE_CALIBRATION=0 to disable calibration).

    Environment variables take precedence over YAML configuration.
    """

    _instance: Optional["ModuleRegistry"] = None
    _modules: Dict[str, Dict] = {}
    _config_path: Optional[Path] = None

    def __new__(cls, config_path: Optional[str] = None) -> "ModuleRegistry":
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the module registry.

        Args:
            config_path: Optional path to modules.yaml file.
                        Defaults to <repo_root>/modules.yaml
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return

        self._initialized = True
        self._modules = {}

        # Determine config path
        if config_path:
            self._config_path = Path(config_path)
        else:
            # Default: look for modules.yaml at repo root
            # Walk up from this file to find repo root
            current = Path(__file__).parent.parent.parent
            self._config_path = current / "modules.yaml"

        self._load_config()
        self._apply_env_overrides()

        logger.info(f"ModuleRegistry initialized with {len(self._modules)} modules")

    def _load_config(self) -> None:
        """Load module configuration from YAML file."""
        if not self._config_path or not self._config_path.exists():
            logger.warning(
                f"Module config not found at {self._config_path}, using defaults"
            )
            self._modules = {}
            return

        try:
            with open(self._config_path, "r") as f:
                config = yaml.safe_load(f)

            if config and "modules" in config:
                self._modules = config["modules"]
                logger.info(f"Loaded module config from {self._config_path}")
            else:
                logger.warning(f"No 'modules' key found in {self._config_path}")
                self._modules = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing modules.yaml: {e}")
            self._modules = {}
        except IOError as e:
            logger.error(f"Error reading modules.yaml: {e}")
            self._modules = {}

    def _apply_env_overrides(self) -> None:
        """
        Apply environment variable overrides to module states.

        Environment variables follow the pattern: MODULE_<NAME>=0|1
        Examples:
            MODULE_CALIBRATION=0  -> Disable calibration module
            MODULE_SAR=1          -> Enable SAR module
        """
        for key, value in os.environ.items():
            if key.startswith("MODULE_"):
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
        if module_key in self._modules:
            old_value = self._modules[module_key].get("enabled", True)
            self._modules[module_key]["enabled"] = enabled
            logger.info(
                f"Module '{module_name}' set enabled={enabled} (was {old_value})"
            )
            return True

        # Create new module entry if it doesn't exist
        self._modules[module_key] = {
            "enabled": enabled,
            "description": f"Runtime-created module '{module_name}'",
        }
        logger.info(f"Module '{module_name}' created with enabled={enabled}")
        return True

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
