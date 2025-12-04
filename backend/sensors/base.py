"""
Base sensor class and result types.

All sensors must inherit from BaseSensor and implement the analyze() method.

Documentation:
- Sensor Framework: Documentation/REUSABLE_CODE_CATALOG.md
- Integration: Documentation/INTEGRATION_GUIDE.md
- Architecture: Documentation/IMPLEMENTATION_SUMMARY.md
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class SensorResult:
    """Standardized result structure for all sensors."""
    sensor_name: str
    passed: Optional[bool] = None  # True/False for pass/fail sensors, None for info-only sensors
    value: float = 0.0
    threshold: float = 0.0
    reason: Optional[str] = None
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Additional sensor-specific data
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary format.

        Uses shared convert_numpy_types from utils.serialization to avoid code duplication.
        """
        from utils.serialization import convert_numpy_types

        result = {
            "sensor_name": self.sensor_name,
            "value": self.value,
            "threshold": self.threshold,
        }

        if self.passed is not None:
            result["passed"] = bool(self.passed)

        if self.reason:
            result["reason"] = str(self.reason)

        if self.detail:
            result["detail"] = str(self.detail)

        if self.metadata:
            result.update(self.metadata)

        # Convert all numpy types to Python native types for JSON serialization
        return convert_numpy_types(result)


class BaseSensor(ABC):
    """
    Abstract base class for all audio sensors.
    
    All sensors must implement the analyze() method which takes audio data
    and sample rate, and returns a SensorResult.
    """
    
    def __init__(self, name: str):
        """
        Initialize sensor.
        
        Args:
            name: Human-readable name of the sensor
        """
        self.name = name
    
    @abstractmethod
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio data and return sensor result.
        
        Args:
            audio_data: Audio signal as numpy array (float32, mono)
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with analysis findings
        """
        pass
    
    def validate_input(self, audio_data: np.ndarray, samplerate: int) -> bool:
        """
        Validate input audio data.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            True if input is valid, False otherwise
        """
        if not isinstance(audio_data, np.ndarray):
            return False
        if len(audio_data) == 0:
            return False
        if samplerate <= 0:
            return False
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

