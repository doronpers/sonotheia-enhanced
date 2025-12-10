"""
Stage 3b: Physics Analysis

Integrates physics-based sensors into the detection pipeline.
Patent-Safe Sensors: Breath (Phonation), Glottal Inertia, Formant Trajectory, etc.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import numpy as np

# Import sensors
from backend.sensors.registry import get_default_sensors, SensorRegistry

logger = logging.getLogger(__name__)


class PhysicsAnalysisStage:
    """
    Stage 3b: Physics Analysis
    
    Runs a suite of patent-safe physics-based sensors to detect
    physiological inconsistencies in the audio.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize physics analysis stage.
        
        Args:
            config: Configuration dictionary (unused for now, uses sensor defaults)
        """
        self.config = config or {}
        self.registry = SensorRegistry()
        
        # Register default patent-safe sensors
        for sensor in get_default_sensors():
            self.registry.register(sensor)
            
        logger.info(f"PhysicsAnalysisStage initialized with {len(self.registry.list_sensors())} sensors")

    def process(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Analyze audio using physics-based sensors.
        
        Args:
            audio: Input audio array
            
        Returns:
            Dictionary containing sensor results
        """
        if audio is None or len(audio) == 0:
            return self._empty_result("Empty audio input")
            
        try:
            # Assume 16kHz sample rate as per pipeline standard
            # Ideally this should be passed in, but the pipeline standardizes on 16kHz
            sample_rate = 16000

            # Risk contribution constants
            PROSECUTION_BASE_INCREMENT = 0.2
            PROSECUTION_MAX_INCREMENT = 0.6
            PROSECUTION_SEVERITY_BONUS = 0.1
            
            # Run all registered sensors
            # analyze_all is async, so we need to run it in an event loop
            results_dict = asyncio.run(self.registry.analyze_all(audio, sample_rate))
            
            # Aggregate results
            detailed_results = {}
            passed_count = 0
            total_score = 0.0
            
            for name, res in results_dict.items():
                if res.value > 0:
                   print(f"DEBUG: {name} raw value: {res.value}")
                # Convert SensorResult to dict
                res_dict = {
                    "passed": res.passed,
                    "score": res.value, 
                    "threshold": res.threshold,
                    "reason": res.reason,
                    "detail": res.detail,
                    "metadata": res.metadata
                }
                detailed_results[name] = res_dict
                
                # Check passed status (some sensors might be None/Info-only)
                if res.passed is True:
                    passed_count += 1
                
                # Normalize score (some sensors return value, not 0-1 probability)
                # This is a heuristic aggregation
                if res.value is not None:
                    # Only count prosecution-category failures toward risk to reduce organic false positives
                    category = self._categorize_sensor(name, res.metadata)
                    if res.passed is False and category == "prosecution":
                        # Scale contribution by severity to still flag clearly synthetic noise
                        severity = res.value
                        if severity < 0.4:
                            increment = PROSECUTION_BASE_INCREMENT
                        else:
                            increment = min(
                                PROSECUTION_MAX_INCREMENT,
                                PROSECUTION_SEVERITY_BONUS + severity,
                            )  # keep bounded
                        total_score += increment  # Prosecution failures add risk
            
            # Cap risk score at 1.0
            physics_score = min(total_score, 1.0)
            
            return {
                "success": True,
                "physics_score": float(physics_score),
                "sensor_results": detailed_results,
                "sensors_passed": passed_count,
                "total_sensors": len(results_dict),
                "is_spoof": physics_score > 0.5
            }

        except Exception as e:
            logger.error(f"Physics analysis failed: {e}")
            return self._empty_result(str(e))

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed analysis."""
        return {
            "success": False,
            "error": error_msg,
            "physics_score": 0.5,
            "sensor_results": {},
            "sensors_passed": 0,
            "total_sensors": 0,
            "is_spoof": False
        }

    def _categorize_sensor(self, name: str, metadata: Optional[Dict[str, Any]]) -> str:
        """
        Infer sensor category (prosecution/defense) based on metadata or name.

        Sensors tagged as prosecution indicate fake evidence; defense indicates real evidence.
        """
        if metadata and metadata.get("category"):
            return metadata.get("category")

        lower = name.lower()
        # Prosecution indicators (risk)
        prosecution_tokens = [
            "pitch", "glottal", "silence", "two", "prosodic",
            "phase", "hf", "deepfake", "artifact"
        ]
        if any(tok in lower for tok in prosecution_tokens):
            return "prosecution"
        return "defense"
