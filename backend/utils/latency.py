"""
Latency profiling and performance optimization utilities.

Provides tools for measuring and optimizing detection pipeline latency
to meet <500ms target for initial screening in financial services.
"""

import time
import logging
from contextlib import contextmanager
from typing import Dict, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LatencyProfile:
    """Latency profile for a detection operation."""
    total_ms: float
    preprocessing_ms: float = 0.0
    encoding_ms: float = 0.0
    sensor_ms: Dict[str, float] = field(default_factory=dict)
    fusion_ms: float = 0.0
    explainability_ms: float = 0.0
    calibration_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_ms": round(self.total_ms, 2),
            "preprocessing_ms": round(self.preprocessing_ms, 2),
            "encoding_ms": round(self.encoding_ms, 2),
            "sensor_ms": {k: round(v, 2) for k, v in self.sensor_ms.items()},
            "fusion_ms": round(self.fusion_ms, 2),
            "explainability_ms": round(self.explainability_ms, 2),
            "calibration_ms": round(self.calibration_ms, 2),
        }
    
    @property
    def meets_target(self) -> bool:
        """Check if latency meets <500ms target."""
        return self.total_ms < 500.0


class LatencyProfiler:
    """Profiles latency across detection pipeline stages."""
    
    def __init__(self):
        """Initialize profiler."""
        self.profile = LatencyProfile(total_ms=0.0)
        self.start_time: Optional[float] = None
    
    @contextmanager
    def stage(self, stage_name: str):
        """Context manager for timing a pipeline stage."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            if stage_name == "preprocessing":
                self.profile.preprocessing_ms = elapsed_ms
            elif stage_name == "encoding":
                self.profile.encoding_ms = elapsed_ms
            elif stage_name == "fusion":
                self.profile.fusion_ms = elapsed_ms
            elif stage_name == "explainability":
                self.profile.explainability_ms = elapsed_ms
            elif stage_name == "calibration":
                self.profile.calibration_ms = elapsed_ms
            elif stage_name.startswith("sensor_"):
                sensor_name = stage_name.replace("sensor_", "")
                self.profile.sensor_ms[sensor_name] = elapsed_ms
    
    def start(self):
        """Start profiling."""
        self.start_time = time.perf_counter()
        self.profile = LatencyProfile(total_ms=0.0)
    
    def finish(self) -> LatencyProfile:
        """Finish profiling and return profile."""
        if self.start_time is not None:
            self.profile.total_ms = (time.perf_counter() - self.start_time) * 1000
        return self.profile


class FastPathDetector:
    """
    Fast-path detector for initial screening (<500ms target).
    
    Uses lightweight sensors and optimized processing to provide
    rapid initial screening before full analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize fast-path detector.
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.max_duration_ms = self.config.get("max_duration_ms", 500.0)
        self.enabled_sensors = self.config.get("enabled_sensors", [
            "breath",  # Fast, physics-based
            "dynamic_range",  # Fast, physics-based
            "bandwidth",  # Fast, spectral analysis
        ])
        self.skip_explainability = self.config.get("skip_explainability", True)
        self.skip_calibration = self.config.get("skip_calibration", True)
    
    def should_use_fast_path(
        self,
        audio_duration_seconds: float,
        file_size_mb: float,
    ) -> bool:
        """
        Determine if fast path should be used.
        
        Args:
            audio_duration_seconds: Audio duration in seconds
            file_size_mb: File size in MB
            
        Returns:
            True if fast path should be used
        """
        # Use fast path for short audio or when explicitly requested
        return (
            audio_duration_seconds <= 10.0 or  # Short audio
            file_size_mb <= 5.0 or  # Small files
            self.config.get("force_fast_path", False)
        )
    
    def get_enabled_sensors(self) -> List[str]:
        """Get list of sensors enabled for fast path."""
        return self.enabled_sensors


def optimize_for_latency(
    audio_data,
    samplerate: int,
    target_duration_ms: float = 500.0,
) -> Dict:
    """
    Optimize audio processing for latency.
    
    Args:
        audio_data: Audio signal
        samplerate: Sample rate
        target_duration_ms: Target processing duration in ms
        
    Returns:
        Optimization configuration
    """
    # Estimate processing time based on audio length
    audio_duration = len(audio_data) / samplerate
    estimated_processing_ms = audio_duration * 50  # Rough estimate: 50ms per second
    
    optimizations = {
        "resample_to_8khz": estimated_processing_ms > target_duration_ms * 0.5,
        "reduce_frame_size": estimated_processing_ms > target_duration_ms * 0.7,
        "skip_alignment": True,  # Skip forced alignment for speed
        "skip_f3": estimated_processing_ms > target_duration_ms * 0.8,
        "batch_sensors": True,
    }
    
    return optimizations
