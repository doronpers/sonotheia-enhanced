"""
Base sensor classes and result structures.

Provides the abstract base class for sensors and a standardized result structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class SensorResult:
    """
    Standardized output structure for sensor analysis.
    
    Attributes:
        sensor_name: Identifier for the sensor
        passed: Pass/fail result (None for info-only sensors)
        value: Measured/calculated value
        threshold: Decision threshold used
        reason: Failure reason code (e.g., "BIOLOGICALLY_IMPOSSIBLE")
        detail: Human-readable explanation
        metadata: Additional data for debugging/logging
    
    Example:
        result = SensorResult(
            sensor_name="breath",
            passed=False,
            value=16.5,
            threshold=14.0,
            reason="BIOLOGICALLY_IMPOSSIBLE",
            detail="Continuous phonation of 16.5s exceeds biological limit of 14.0s"
        )
    """
    sensor_name: str
    passed: Optional[bool]
    value: float
    threshold: float
    reason: Optional[str] = None
    detail: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "sensor_name": self.sensor_name,
            "passed": self.passed,
            "value": self.value,
            "threshold": self.threshold,
            "reason": self.reason,
            "detail": self.detail,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensorResult":
        """Create SensorResult from dictionary."""
        return cls(
            sensor_name=data.get("sensor_name", "unknown"),
            passed=data.get("passed"),
            value=data.get("value", 0.0),
            threshold=data.get("threshold", 0.0),
            reason=data.get("reason"),
            detail=data.get("detail"),
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "PASS" if self.passed else ("FAIL" if self.passed is False else "INFO")
        return f"{self.sensor_name}: {status} (value={self.value}, threshold={self.threshold})"


class BaseSensor(ABC):
    """
    Abstract base class defining the sensor interface.
    
    Sensors are independent, pluggable analysis modules that can be
    registered with a SensorRegistry for coordinated execution.
    
    Subclasses must implement the `analyze` method.
    
    Example:
        class BreathSensor(BaseSensor):
            def __init__(self, max_phonation_seconds: float = 14.0):
                super().__init__(name="breath")
                self._max_phonation = max_phonation_seconds
            
            def analyze(self, audio_data, samplerate: int) -> SensorResult:
                # Analysis logic here
                max_phonation = calculate_max_phonation(audio_data, samplerate)
                passed = max_phonation <= self._max_phonation
                
                return SensorResult(
                    sensor_name=self.name,
                    passed=passed,
                    value=max_phonation,
                    threshold=self._max_phonation,
                    reason="BIOLOGICALLY_IMPOSSIBLE" if not passed else None,
                    detail=f"Max phonation: {max_phonation:.1f}s"
                )
    """
    
    def __init__(self, name: str):
        """
        Initialize the sensor.
        
        Args:
            name: Unique identifier for this sensor
        """
        self._name = name
    
    @property
    def name(self) -> str:
        """Get the sensor's unique name."""
        return self._name
    
    @abstractmethod
    def analyze(self, data: Any, context: Any) -> SensorResult:
        """
        Analyze input data and return a result.
        
        Args:
            data: Input data to analyze (type depends on sensor)
            context: Additional context (e.g., samplerate for audio)
        
        Returns:
            SensorResult with analysis findings
        
        Raises:
            ValueError: If input data is invalid
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}')"


class InfoSensor(BaseSensor):
    """
    Base class for sensors that only provide information, not pass/fail.
    
    Info sensors always return passed=None and are not considered
    in verdict calculations.
    
    Example:
        class MetadataSensor(InfoSensor):
            def __init__(self):
                super().__init__(name="metadata")
            
            def analyze(self, data, context) -> SensorResult:
                return SensorResult(
                    sensor_name=self.name,
                    passed=None,  # Info-only
                    value=len(data),
                    threshold=0,
                    detail=f"Data length: {len(data)}"
                )
    """
    
    def analyze(self, data: Any, context: Any) -> SensorResult:
        """Default implementation - subclasses should override."""
        return SensorResult(
            sensor_name=self.name,
            passed=None,
            value=0.0,
            threshold=0.0,
            detail="Info sensor - override analyze() method",
        )


class ThresholdSensor(BaseSensor):
    """
    Base class for sensors that compare a value against a threshold.
    
    Simplifies creating sensors where the pass/fail decision is based
    on whether a computed value is below or above a threshold.
    
    Example:
        class QualitySensor(ThresholdSensor):
            def __init__(self):
                super().__init__(
                    name="quality",
                    threshold=0.5,
                    passes_when_below=False  # Higher is better
                )
            
            def compute_value(self, data, context) -> float:
                return calculate_quality_score(data)
    """
    
    def __init__(
        self,
        name: str,
        threshold: float,
        passes_when_below: bool = True,
    ):
        """
        Initialize threshold sensor.
        
        Args:
            name: Sensor identifier
            threshold: Decision threshold
            passes_when_below: If True, passes when value < threshold
        """
        super().__init__(name)
        self._threshold = threshold
        self._passes_when_below = passes_when_below
    
    @property
    def threshold(self) -> float:
        """Get the decision threshold."""
        return self._threshold
    
    @abstractmethod
    def compute_value(self, data: Any, context: Any) -> float:
        """
        Compute the value to compare against threshold.
        
        Args:
            data: Input data
            context: Additional context
        
        Returns:
            Computed numeric value
        """
        pass
    
    def analyze(self, data: Any, context: Any) -> SensorResult:
        """
        Analyze data by computing value and comparing to threshold.
        
        Returns:
            SensorResult with pass/fail based on threshold comparison
        """
        value = self.compute_value(data, context)
        
        if self._passes_when_below:
            passed = value <= self._threshold
        else:
            passed = value >= self._threshold
        
        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=value,
            threshold=self._threshold,
            reason=self._get_failure_reason() if not passed else None,
            detail=self._build_detail(value, passed),
        )
    
    def _get_failure_reason(self) -> str:
        """Get reason code for failure. Override in subclasses."""
        return "THRESHOLD_EXCEEDED"
    
    def _build_detail(self, value: float, passed: bool) -> str:
        """Build detail message. Override in subclasses for custom messages."""
        status = "passed" if passed else "failed"
        comparison = "<=" if self._passes_when_below else ">="
        return f"{self.name}: value {value:.3f} {comparison} threshold {self._threshold:.3f} ({status})"
