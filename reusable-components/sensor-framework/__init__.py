"""
Sensor Framework - Reusable plugin architecture for analysis systems.

A flexible, extensible sensor framework for building plugin-based analysis systems.
Originally designed for audio authenticity detection but applicable to any domain
requiring modular validation/analysis.

Exports:
    - BaseSensor: Abstract base class for sensors
    - SensorResult: Standardized result structure
    - SensorRegistry: Centralized sensor management
"""

from .base import BaseSensor, SensorResult
from .registry import SensorRegistry

__all__ = [
    "BaseSensor",
    "SensorResult",
    "SensorRegistry",
]

__version__ = "1.0.0"
