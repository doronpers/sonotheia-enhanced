"""
Sensor registry for centralized sensor management and orchestration.

Provides dynamic registration, ordered execution, and verdict aggregation.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from .base import BaseSensor, SensorResult


# Type alias for custom verdict aggregator functions
VerdictAggregator = Callable[[Dict[str, SensorResult]], Tuple[str, str]]


class SensorRegistry:
    """
    Centralized sensor management and orchestration.
    
    Hybrid design: OOP for state management, FP for data flow.
    
    Features:
        - Dynamic registration/unregistration
        - Ordered execution
        - Error isolation (one sensor failure doesn't stop others)
        - Configurable verdict aggregation
        - Fluent interface for chaining
    
    Example:
        # Create and configure registry
        registry = (SensorRegistry()
            .register(BreathSensor(), "breath")
            .register(DynamicRangeSensor(), "dynamic_range")
            .register(BandwidthSensor(), "bandwidth"))
        
        # Run analysis
        results = registry.analyze_all(audio_data, samplerate)
        
        # Get verdict
        verdict, detail = registry.get_verdict(results)
    """
    
    def __init__(self):
        """Initialize an empty sensor registry."""
        self._sensors: Dict[str, BaseSensor] = {}
        self._sensor_order: List[str] = []
    
    def register(
        self,
        sensor: BaseSensor,
        name: Optional[str] = None,
    ) -> "SensorRegistry":
        """
        Register a sensor with the registry.
        
        Fluent interface returns self for method chaining.
        
        Args:
            sensor: Sensor instance to register
            name: Optional override for sensor name
        
        Returns:
            Self for chaining
        
        Example:
            registry.register(MySensor(), "my_sensor")
        """
        sensor_name = name or sensor.name
        self._sensors[sensor_name] = sensor
        if sensor_name not in self._sensor_order:
            self._sensor_order.append(sensor_name)
        return self
    
    def unregister(self, name: str) -> "SensorRegistry":
        """
        Remove a sensor from the registry.
        
        Args:
            name: Name of sensor to remove
        
        Returns:
            Self for chaining
        """
        if name in self._sensors:
            del self._sensors[name]
        if name in self._sensor_order:
            self._sensor_order.remove(name)
        return self
    
    def get_sensor(self, name: str) -> Optional[BaseSensor]:
        """Get a registered sensor by name."""
        return self._sensors.get(name)
    
    def list_sensors(self) -> List[str]:
        """List all registered sensor names in order."""
        return list(self._sensor_order)
    
    def analyze_all(
        self,
        data: Any,
        context: Any,
        sensor_names: Optional[List[str]] = None,
    ) -> Dict[str, SensorResult]:
        """
        Run all (or specified) sensors and collect results.
        
        Errors in individual sensors are caught and recorded, not raised.
        
        Args:
            data: Input data to analyze
            context: Additional context (e.g., samplerate)
            sensor_names: Optional list of specific sensors to run
        
        Returns:
            Dictionary mapping sensor names to their results
        
        Example:
            # Run all sensors
            results = registry.analyze_all(audio_data, samplerate)
            
            # Run specific sensors
            results = registry.analyze_all(
                audio_data, samplerate,
                sensor_names=["breath", "bandwidth"]
            )
        """
        sensors_to_run = sensor_names or self._sensor_order
        
        return {
            name: self._safe_analyze(name, data, context)
            for name in sensors_to_run
            if name in self._sensors
        }
    
    def _safe_analyze(
        self,
        name: str,
        data: Any,
        context: Any,
    ) -> SensorResult:
        """
        Safely run a single sensor with error handling.
        
        Catches any exceptions and returns an error result.
        """
        try:
            sensor = self._sensors[name]
            return sensor.analyze(data, context)
        except Exception as e:
            return SensorResult(
                sensor_name=name,
                passed=None,
                value=0.0,
                threshold=0.0,
                reason="ERROR",
                detail=f"Sensor analysis failed: {str(e)}",
                metadata={"error_type": type(e).__name__},
            )
    
    def get_verdict(
        self,
        results: Dict[str, SensorResult],
        fail_on_any: bool = True,
        aggregator: Optional[VerdictAggregator] = None,
    ) -> Tuple[str, str]:
        """
        Calculate overall verdict from sensor results.
        
        Supports custom aggregation logic via the aggregator parameter.
        
        Args:
            results: Dictionary of sensor results
            fail_on_any: If True, fail if any sensor fails
            aggregator: Optional custom function for verdict calculation
        
        Returns:
            Tuple of (verdict, detail) strings
        
        Example:
            verdict, detail = registry.get_verdict(results)
            
            # With custom aggregator
            def custom_verdict(results):
                failures = sum(1 for r in results.values() if not r.passed)
                if failures > 2:
                    return "SUSPICIOUS", f"{failures} sensors failed"
                return "REAL", "Acceptable results"
            
            verdict, detail = registry.get_verdict(results, aggregator=custom_verdict)
        """
        if aggregator:
            return aggregator(results)
        
        return self._default_verdict_logic(results, fail_on_any)
    
    def _default_verdict_logic(
        self,
        results: Dict[str, SensorResult],
        fail_on_any: bool,
    ) -> Tuple[str, str]:
        """
        Default verdict calculation using functional patterns.
        
        Filters info-only sensors and aggregates pass/fail results.
        """
        # Filter to only pass/fail sensors (exclude info-only)
        pass_fail_results = {
            name: result
            for name, result in results.items()
            if result.passed is not None
        }
        
        if not pass_fail_results:
            return "UNKNOWN", "No sensor results available"
        
        # Find failures
        failures = [
            (name, result)
            for name, result in pass_fail_results.items()
            if not result.passed
        ]
        
        if failures and fail_on_any:
            name, result = failures[0]
            verdict = result.reason or "SYNTHETIC"
            detail = result.detail or f"{name} failed validation"
            return verdict, detail
        
        # All passed
        return "REAL", "All physics checks passed."
    
    def get_summary(
        self,
        results: Dict[str, SensorResult],
    ) -> Dict[str, Any]:
        """
        Get a summary of all results.
        
        Args:
            results: Dictionary of sensor results
        
        Returns:
            Summary dictionary with counts and details
        """
        passed_count = sum(1 for r in results.values() if r.passed is True)
        failed_count = sum(1 for r in results.values() if r.passed is False)
        info_count = sum(1 for r in results.values() if r.passed is None)
        
        failed_sensors = [
            name for name, r in results.items() if r.passed is False
        ]
        
        return {
            "total_sensors": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "info_only": info_count,
            "failed_sensors": failed_sensors,
            "pass_rate": passed_count / (passed_count + failed_count) if (passed_count + failed_count) > 0 else 0.0,
        }
    
    def __len__(self) -> int:
        """Return number of registered sensors."""
        return len(self._sensors)
    
    def __contains__(self, name: str) -> bool:
        """Check if a sensor is registered."""
        return name in self._sensors
    
    def __repr__(self) -> str:
        return f"SensorRegistry(sensors={list(self._sensors.keys())})"
