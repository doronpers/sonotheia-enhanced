"""
Sensor registry for managing and orchestrating multiple sensors.

Provides a centralized way to register, configure, and run sensors.
Supports both synchronous and asynchronous sensors.
"""

import inspect
import time
from contextlib import contextmanager, nullcontext
from typing import Dict, List, Optional, Any
try:
    import numpy as np
except ImportError:
    np = None  # numpy may not be available in linting environment
from .base import BaseSensor, SensorResult


@contextmanager
def time_sensor(sensor_name: str, metrics=None):
    """Context manager to time sensor execution."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        if metrics is not None:
            metrics.record_sensor_timing(sensor_name, duration)


def get_default_sensors() -> List[BaseSensor]:
    """
    Get the default list of sensors for audio analysis.
    
    Returns sensors in recommended order for analysis pipeline:
    1. Physics-based sensors (breath, dynamic_range, bandwidth)
    2. RecApp detection modules (phase_coherence, vocal_tract, coarticulation)
    3. AI model sensors (hf_deepfake) - acts as tie-breaker after physics checks
    
    Returns:
        List of sensor instances in analysis order
    """
    from .breath import BreathSensor
    from .dynamic_range import DynamicRangeSensor
    from .bandwidth import BandwidthSensor
    from .phase_coherence import PhaseCoherenceSensor
    from .glottal_inertia import GlottalInertiaSensor
    from .digital_silence import DigitalSilenceSensor
    from .global_formants import GlobalFormantSensor
    from .coarticulation import CoarticulationSensor
    from .formant import FormantTrajectorySensor
    from .hf_deepfake import HFDeepfakeSensor
    
    return [
        BreathSensor(),
        DynamicRangeSensor(),
        BandwidthSensor(),
        PhaseCoherenceSensor(),
        GlottalInertiaSensor(),
        DigitalSilenceSensor(),
        GlobalFormantSensor(),
        CoarticulationSensor(),
        FormantTrajectorySensor(),
        HFDeepfakeSensor(),  # AI model sensor - after PhaseCoherenceSensor for tie-breaking
    ]


class SensorRegistry:
    """
    Registry for managing audio sensors.
    
    Allows registration of sensors and orchestration of analysis pipelines.
    Supports both pass/fail sensors and info-only sensors.
    """
    
    def __init__(self):
        """Initialize sensor registry."""
        self._sensors: Dict[str, BaseSensor] = {}
        self._sensor_order: List[str] = []
    
    def register(self, sensor: BaseSensor, name: Optional[str] = None) -> None:
        """
        Register a sensor with the registry.
        
        Args:
            sensor: Sensor instance to register
            name: Optional custom name (defaults to sensor.name)
        """
        sensor_name = name or sensor.name
        self._sensors[sensor_name] = sensor
        if sensor_name not in self._sensor_order:
            self._sensor_order.append(sensor_name)
    
    def unregister(self, name: str) -> None:
        """
        Unregister a sensor from the registry.
        
        Args:
            name: Name of sensor to remove
        """
        if name in self._sensors:
            del self._sensors[name]
            if name in self._sensor_order:
                self._sensor_order.remove(name)
    
    def get_sensor(self, name: str) -> Optional[BaseSensor]:
        """
        Get a sensor by name.
        
        Args:
            name: Name of sensor to retrieve
            
        Returns:
            Sensor instance or None if not found
        """
        return self._sensors.get(name)
    
    def list_sensors(self) -> List[str]:
        """
        List all registered sensor names.
        
        Returns:
            List of sensor names in registration order
        """
        return self._sensor_order.copy()
    
    async def analyze_all(
        self,
        audio_data: np.ndarray,
        samplerate: int,
        sensor_names: Optional[List[str]] = None,
        metrics: Optional[Any] = None
    ) -> Dict[str, SensorResult]:
        """
        Run all registered sensors (or specified subset) on audio data.

        Supports both synchronous and asynchronous sensors. Async sensors
        (like HFDeepfakeSensor) will be properly awaited, while sync sensors
        run normally.

        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            sensor_names: Optional list of sensor names to run (defaults to all)
            metrics: Optional MetricsCollector instance for timing measurements

        Returns:
            Dictionary mapping sensor names to their results
        """
        sensors_to_run = sensor_names or self._sensor_order
        results = {}

        for name in sensors_to_run:
            if name in self._sensors:
                try:
                    sensor = self._sensors[name]
                    # Time sensor execution if metrics provided
                    timing_context = time_sensor(name, metrics) if metrics else nullcontext()
                    with timing_context:
                        # Check if the analyze method is async
                        if inspect.iscoroutinefunction(sensor.analyze):
                            # Await async sensors
                            result = await sensor.analyze(audio_data, samplerate)
                        else:
                            # Call sync sensors normally
                            result = sensor.analyze(audio_data, samplerate)
                    results[name] = result
                except Exception as e:
                    # Create error result
                    results[name] = SensorResult(
                        sensor_name=name,
                        passed=None,
                        value=0.0,
                        threshold=0.0,
                        reason="ERROR",
                        detail=f"Sensor analysis failed: {str(e)}"
                    )

        return results
    
    def get_verdict(
        self,
        results: Dict[str, SensorResult],
        fail_on_any: Optional[bool] = None
    ) -> tuple[str, str]:
        """
        Determine overall verdict from sensor results.
        
        Uses configurable verdict logic from settings.yaml:
        - fail_on_any=True: Any failed sensor results in SYNTHETIC verdict (legacy)
        - fail_on_any=False: Uses weighted or minimum-fail-count logic
        
        When fail_on_any is False (default from config):
        - use_weighted_verdict=True: Sum of weights of failed sensors must exceed threshold
        - use_weighted_verdict=False: Count of failed sensors must reach min_fail_count
        
        Args:
            results: Dictionary of sensor results
            fail_on_any: If True, any failed sensor results in SYNTHETIC verdict.
                         If None, uses value from config/settings.yaml (default: False)
            
        Returns:
            Tuple of (verdict, detail) where verdict is "REAL" or reason code
        """
        from utils.config import get_verdict_config
        
        if not results:
            return "UNKNOWN", "No sensor results available"
        
        # Load verdict config
        verdict_config = get_verdict_config()
        
        # Use passed parameter if provided, otherwise use config
        if fail_on_any is None:
            fail_on_any = verdict_config.get("fail_on_any", False)
        
        min_fail_count = verdict_config.get("min_fail_count", 2)
        use_weighted = verdict_config.get("use_weighted_verdict", True)
        sensor_weights = verdict_config.get("sensor_weights", {})
        weighted_threshold = verdict_config.get("weighted_threshold", 1.5)
        
        verdict = "REAL"
        details = []
        failed_sensors = []
        
        for name, result in results.items():
            # Skip info-only sensors (passed is None)
            if result.passed is None:
                continue
            
            if not result.passed:
                failed_sensors.append((name, result))
                details.append(result.detail or f"{name} failed validation")
                
                if fail_on_any:
                    # Legacy mode: fail on first failure
                    verdict = result.reason or "SYNTHETIC"
                    break
        
        # If not using fail_on_any, apply weighted or min-fail-count logic
        if not fail_on_any and failed_sensors:
            if use_weighted:
                # Calculate weighted sum of failed sensors
                weighted_sum = 0.0
                for name, result in failed_sensors:
                    weight = sensor_weights.get(name, 1.0)
                    weighted_sum += weight
                
                if weighted_sum >= weighted_threshold:
                    # Use the most significant failure reason
                    verdict = failed_sensors[0][1].reason or "SYNTHETIC"
            else:
                # Simple count-based logic
                if len(failed_sensors) >= min_fail_count:
                    verdict = failed_sensors[0][1].reason or "SYNTHETIC"
        
        detail = " ".join(details) if details else "All physics checks passed."
        
        return verdict, detail
    
    def __len__(self) -> int:
        """Return number of registered sensors."""
        return len(self._sensors)
    
    def __contains__(self, name: str) -> bool:
        """Check if sensor is registered."""
        return name in self._sensors

