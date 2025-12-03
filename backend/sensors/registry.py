import asyncio
import logging
from typing import Dict, List, Type, Optional, Any, Tuple
import io
import numpy as np
import soundfile as sf
import librosa
import numpy as np

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

class SensorRegistry:
    """
    Registry for managing and executing sensors.
    """
    
    def __init__(self):
        self._sensors: Dict[str, BaseSensor] = {}

    def register(self, sensor_class: Type[BaseSensor], name: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Register a sensor class.
        """
        sensor_instance = sensor_class(config=config)
        sensor_name = name or sensor_instance.__class__.__name__
        self._sensors[sensor_name] = sensor_instance
        logger.info(f"Registered sensor: {sensor_name}")

    def get_sensor(self, name: str) -> Optional[BaseSensor]:
        """Retrieve a registered sensor by name.

        Args:
            name: The identifier of the sensor.
        Returns:
            The sensor instance if registered, otherwise ``None``.
        """
        return self._sensors.get(name)

    async def analyze_all(self, audio_data: np.ndarray, samplerate: int, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Run all registered sensors concurrently with a timeout.
        """
        results = {}
        
        async def run_sensor(name: str, sensor: BaseSensor):
            try:
                # Run synchronous analyze method in thread pool to avoid blocking
                # Use asyncio.wait_for to enforce timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(sensor.analyze, audio_data, samplerate),
                    timeout=timeout
                )
                return name, result.to_dict()
            except asyncio.TimeoutError:
                logger.error(f"Sensor {name} timed out after {timeout}s")
                error_result = SensorResult(
                    sensor_name=name,
                    passed=None,
                    value=0.0,
                    threshold=0.0,
                    reason="Timeout",
                    detail=f"Execution exceeded {timeout}s",
                    metadata={"error": "Timeout"}
                )
                return name, error_result.to_dict()
            except Exception as e:
                logger.error(f"Error running sensor {name}: {e}", exc_info=True)
                # Return error result
                error_result = SensorResult(
                    sensor_name=name,
                    passed=None,
                    value=0.0,
                    threshold=0.0,
                    reason=f"Error: {str(e)}",
                    detail="Sensor execution failed",
                    metadata={"error": str(e)}
                )
                return name, error_result.to_dict()

        # Create tasks for all sensors
        tasks = [run_sensor(name, sensor) for name, sensor in self._sensors.items()]
        
        if not tasks:
            return {}

        # Run all tasks concurrently
        sensor_results = await asyncio.gather(*tasks)
        
        for name, result in sensor_results:
            results[name] = result
            
        return results
