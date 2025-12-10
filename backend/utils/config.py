"""
Configuration loader for Sonotheia backend.

Loads sensor thresholds and other settings from config/settings.yaml.
Provides default values if config file is not found or values are missing.
"""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

# Path to settings.yaml (relative to backend directory)
# Using .resolve() for more robust path handling
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"

# Thread-safe cached settings
_settings_cache: Optional[Dict[str, Any]] = None
_settings_lock = threading.Lock()


def load_settings(reload: bool = False) -> Dict[str, Any]:
    """
    Load settings from config/settings.yaml.

    Thread-safe implementation using a lock to prevent race conditions.

    Args:
        reload: If True, force reload from disk even if cached.

    Returns:
        Dictionary of settings.
    """
    global _settings_cache

    with _settings_lock:
        if _settings_cache is not None and not reload:
            return _settings_cache

        settings: Dict[str, Any] = {}

        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = yaml.safe_load(f) or {}
                logger.info(f"Loaded settings from {SETTINGS_FILE}")
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse settings.yaml: {e}")
            except Exception as e:
                logger.error(f"Failed to load settings.yaml: {e}")
        else:
            logger.warning(f"Settings file not found: {SETTINGS_FILE}")

        _settings_cache = settings
        return settings


def get_sensor_thresholds() -> Dict[str, Any]:
    """
    Get sensor threshold configuration.

    Returns:
        Dictionary of sensor thresholds with defaults.
    """
    settings = load_settings()
    # Support both "sensors" (new standard) and "sensor_thresholds" (legacy)
    sensor_config = settings.get("sensors", {}) or settings.get("sensor_thresholds", {})

    # Default values - used if not specified in config
    defaults = {
        "dynamic_range": {
            "crest_factor_threshold": 5.0,  # Lowered from 12.0 to reduce false positives
        },
        "breath": {
            "max_phonation_seconds": 14.0,
            "silence_threshold_db": -60,
            "frame_size_seconds": 0.02,
        },
        "bandwidth": {
            "rolloff_threshold_hz": 4000,
            "rolloff_percent": 0.90,
            "contribute_to_verdict": True,  # Narrowband detection now contributes to verdict
        },
        "phase_coherence": {
            "plv_natural_min": 0.7,
            "plv_synthetic_max": 0.5,
            "phase_jump_rate_threshold": 0.15,
            "suspicion_threshold": 0.5,
        },
        "vocal_tract": {
            "min_cm": 12.0,
            "max_cm": 20.0,
            "impossible_threshold_cm": 25.0,
        },
        "coarticulation": {
            "max_formant_velocity_hz_ms": 300,
            "min_transition_duration_ms": 20,
            "max_transition_duration_ms": 150,
            "min_formant_continuity": 0.7,
        },
        "verdict": {
            "fail_on_any": False,  # Changed from True to require weighted/minimum fails
            "min_fail_count": 2,  # Minimum sensors that must fail to trigger SYNTHETIC
            "use_weighted_verdict": True,  # Enable weighted scoring for verdict
            "sensor_weights": {
                "breath": 1.0,
                "dynamic_range": 1.0,
                "bandwidth": 0.5,  # Lower weight for bandwidth (info-like)
                "phase_coherence": 0.8,
                "vocal_tract": 1.0,
                "coarticulation": 0.7,
                # HF AI model weight allows solo SYNTHETIC verdict when AI detects fake
                "hf_deepfake": 1.5,
            },
            "weighted_threshold": 1.5,  # Sum of weights must exceed this for SYNTHETIC
        },
    }

    # Merge config with defaults (config values override defaults)
    # Merge defaults and config
    result = defaults.copy()
    
    for sensor_name, config_values in sensor_config.items():
        if sensor_name not in result:
            result[sensor_name] = config_values
        elif isinstance(result[sensor_name], dict) and isinstance(config_values, dict):
             # Deep merge for dictionary values
             result[sensor_name] = {**result[sensor_name], **config_values}
        else:
             # Overwrite non-dict values
             result[sensor_name] = config_values

    return result


def get_threshold(sensor_name: str, threshold_name: str, default: Any = None) -> Any:
    """
    Get a specific threshold value for a sensor.

    Args:
        sensor_name: Name of the sensor (e.g., 'dynamic_range', 'breath')
        threshold_name: Name of the threshold (e.g., 'crest_factor_threshold')
        default: Default value if not found

    Returns:
        Threshold value or default.
    """
    thresholds = get_sensor_thresholds()
    sensor_thresholds = thresholds.get(sensor_name, {})

    if isinstance(sensor_thresholds, dict):
        return sensor_thresholds.get(threshold_name, default)
    return default


def get_verdict_config() -> Dict[str, Any]:
    """
    Get verdict configuration.

    Returns:
        Dictionary with verdict settings.
    """
    settings = load_settings()

    # Try new structure first (verdict_logic)
    verdict_config = settings.get("verdict_logic", {})

    # Fallback to old structure (sensor_thresholds.verdict)
    if not verdict_config:
        thresholds = get_sensor_thresholds()
        verdict_config = thresholds.get("verdict", {})

    # Default values if neither structure found
    if not verdict_config:
        verdict_config = {
            "fail_on_any": False,
            "min_fail_count": 2,
            "use_weighted_verdict": True,
            "sensor_weights": {},
            "weighted_threshold": 1.5,
        }

    return verdict_config


def get_fusion_config() -> Dict[str, Any]:
    """
    Get fusion configuration from settings.yaml.

    Returns:
        Dictionary containing fusion configuration with profiles and weights.
    """
    settings = load_settings()
    fusion_config = settings.get("fusion", {})

    # Default fusion config if not found
    if not fusion_config:
        fusion_config = {
            "profiles": {
                "default": {
                    "weights": {},
                    "thresholds": {
                        "synthetic": 0.7,
                        "real": 0.3
                    }
                }
            }
        }

    return fusion_config


def get_sensor_weights(profile: str = "default") -> Dict[str, float]:
    """
    Get sensor weights for a specific fusion profile.

    Args:
        profile: Profile name (default, narrowband, etc.)

    Returns:
        Dictionary mapping sensor names to weights.
    """
    fusion_config = get_fusion_config()
    profiles = fusion_config.get("profiles", {})
    profile_config = profiles.get(profile, {})
    weights = profile_config.get("weights", {})

    # Default weights if profile not found
    if not weights:
        logger.warning(f"No weights found for profile '{profile}', using defaults")
        weights = {
            "GlottalInertiaSensor": 0.35,
            "PitchVelocitySensor": 0.15,
            "FormantTrajectorySensor": 0.20,
            "DigitalSilenceSensor": 0.15,
            "GlobalFormantSensor": 0.10,
            "CoarticulationSensor": 0.05,
        }

    return weights


def get_fusion_thresholds(profile: str = "default") -> Dict[str, float]:
    """
    Get fusion decision thresholds for a specific profile.

    Args:
        profile: Profile name (default, narrowband, etc.)

    Returns:
        Dictionary with 'synthetic' and 'real' thresholds.
    """
    fusion_config = get_fusion_config()
    profiles = fusion_config.get("profiles", {})
    profile_config = profiles.get(profile, {})
    thresholds = profile_config.get("thresholds", {})

    # Default thresholds
    if not thresholds:
        thresholds = {
            "synthetic": 0.7,
            "real": 0.3
        }

    return thresholds
