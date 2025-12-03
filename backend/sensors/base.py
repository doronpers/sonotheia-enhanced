from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
import numpy as np

@dataclass
class SensorResult:
    """
    Standardized sensor result dataclass.
    Used internally by sensors before conversion to Pydantic model.
    """
    sensor_name: str
    passed: Optional[bool]
    value: float
    threshold: float
    reason: Optional[str] = None
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaseSensor(ABC):
    """
    Abstract base class for all sensors.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio data and return a SensorResult.
        
        Args:
            audio_data: float32 mono numpy array of audio samples
            samplerate: sample rate in Hz
            
        Returns:
            SensorResult object
        """
        pass
