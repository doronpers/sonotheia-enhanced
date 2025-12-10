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

            # Run all registered sensors
            # analyze_all is async, so we need to run it in an event loop
            results_dict = asyncio.run(self.registry.analyze_all(audio, sample_rate))

            # Load sensor weights from config
            from backend.utils.config import get_sensor_weights, get_fusion_thresholds

            # Detect codec/bandwidth to select appropriate profile
            bandwidth_result = results_dict.get("BandwidthSensor")
            is_narrowband = False
            if bandwidth_result and bandwidth_result.value is not None:
                # BandwidthSensor returns rolloff frequency
                # <4kHz rolloff = narrowband (phone/VoIP)
                if bandwidth_result.value < 4000:
                    is_narrowband = True
                    logger.info("Narrowband audio detected, using narrowband fusion profile")

            # Select fusion profile based on bandwidth
            profile = "narrowband" if is_narrowband else "default"
            sensor_weights = get_sensor_weights(profile=profile)
            fusion_thresholds = get_fusion_thresholds(profile=profile)

            # Aggregate results using WEIGHTED fusion
            detailed_results = {}
            passed_count = 0
            weighted_sum = 0.0
            total_weight = 0.0

            for name, res in results_dict.items():
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

                # Get weight for this sensor (default to 0.05 for unknown sensors)
                weight = sensor_weights.get(name, 0.05)

                # Skip disabled sensors (weight = 0) or info-only sensors (passed = None)
                if weight == 0 or res.passed is None:
                    continue

                # Convert boolean passed status to risk score
                # passed=True (real) → risk=0.0
                # passed=False (spoof) → risk=1.0
                risk_score = 0.0 if res.passed else 1.0

                # Apply weight
                weighted_sum += risk_score * weight
                total_weight += weight

            # Normalize by total weight
            if total_weight == 0:
                logger.warning("Total sensor weight is zero, using default score")
                physics_score = 0.5
            else:
                physics_score = weighted_sum / total_weight

            # Cap risk score at [0.0, 1.0]
            physics_score = max(0.0, min(1.0, physics_score))

            # Use adaptive threshold from config
            synthetic_threshold = fusion_thresholds.get("synthetic", 0.7)

            return {
                "success": True,
                "physics_score": float(physics_score),
                "sensor_results": detailed_results,
                "sensors_passed": passed_count,
                "total_sensors": len(results_dict),
                "total_weight": float(total_weight),
                "profile": profile,
                "is_spoof": physics_score > synthetic_threshold
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
