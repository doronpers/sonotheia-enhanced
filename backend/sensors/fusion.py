"""
Multi-Sensor Fusion Engine

Implements weighted scoring logic to combine multiple sensor results into
a unified risk assessment with explainable contributing factors.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from backend.sensors.base import SensorResult

logger = logging.getLogger(__name__)


# Default sensor weights (can be overridden via config)
DEFAULT_WEIGHTS = {
    "BreathSensor": 0.30,
    "BandwidthSensor": 0.25,
    "DynamicRangeSensor": 0.25,
    "PhaseCoherenceSensor": 0.10,
    "HuggingFaceDetector": 0.10,
    # Fallback weight for unknown sensors
    "_default": 0.05,
}

# Verdict thresholds
THRESHOLD_SYNTHETIC = 0.7  # Score > 0.7 = SYNTHETIC
THRESHOLD_REAL = 0.3       # Score < 0.3 = REAL
# 0.3 <= score <= 0.7 = SUSPICIOUS


def calculate_fusion_verdict(
    results: List[SensorResult],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate weighted fusion verdict from multiple sensor results.
    
    Args:
        results: List of SensorResult objects from individual sensors
        weights: Optional custom weight dictionary (sensor_name -> weight)
        
    Returns:
        Dictionary containing:
            - global_risk_score: Weighted average risk score (0.0-1.0)
            - verdict: "SYNTHETIC", "REAL", or "SUSPICIOUS"
            - contributing_factors: List of sensors with their contributions
            - confidence: Confidence level based on sensor consensus
            - metadata: Additional information about the fusion process
    """
    # Input validation
    if not isinstance(results, list):
        logger.error("Results must be a list")
        return {
            "global_risk_score": 0.5,
            "verdict": "UNKNOWN",
            "contributing_factors": [],
            "confidence": 0.0,
            "metadata": {"error": "Invalid input type"}
        }
    
    if not results:
        logger.warning("No sensor results provided to fusion engine")
        return {
            "global_risk_score": 0.5,
            "verdict": "UNKNOWN",
            "contributing_factors": [],
            "confidence": 0.0,
            "metadata": {"error": "No sensor results available"}
        }
    
    # Use provided weights or defaults
    sensor_weights = weights or DEFAULT_WEIGHTS
    
    # Validate custom weights if provided
    if weights:
        if not isinstance(weights, dict):
            logger.error("Weights must be a dictionary")
            sensor_weights = DEFAULT_WEIGHTS
        else:
            # Ensure all weights are numeric and non-negative
            for sensor_name, weight in weights.items():
                if not isinstance(weight, (int, float)) or weight < 0:
                    logger.warning(f"Invalid weight for {sensor_name}: {weight}. Using default.")
                    sensor_weights = DEFAULT_WEIGHTS
                    break
    
    # Calculate weighted risk score
    total_weight = 0.0
    weighted_sum = 0.0
    contributing_factors = []
    
    for result in results:
        # Skip sensors that didn't complete (passed=None means skipped/error)
        if result.passed is None:
            logger.debug(f"Skipping sensor {result.sensor_name} (not completed)")
            continue
            
        # Get weight for this sensor
        weight = sensor_weights.get(
            result.sensor_name,
            sensor_weights.get("_default", 0.05)
        )
        
        # Convert boolean 'passed' to risk score
        # passed=True (real) -> risk_score=0.0
        # passed=False (spoof) -> risk_score=1.0
        risk_score = 0.0 if result.passed else 1.0
        
        # Apply weight
        weighted_sum += risk_score * weight
        total_weight += weight
        
        # Track contributing factors
        contributing_factors.append({
            "sensor_name": result.sensor_name,
            "risk_score": risk_score,
            "weight": weight,
            "contribution": risk_score * weight,
            "value": result.value,
            "threshold": result.threshold,
            "reason": result.reason,
            "detail": result.detail
        })
    
    # Normalize by total weight
    if total_weight == 0:
        logger.warning("Total sensor weight is zero")
        global_risk_score = 0.5
    else:
        global_risk_score = weighted_sum / total_weight
    
    # Determine verdict based on thresholds
    if global_risk_score > THRESHOLD_SYNTHETIC:
        verdict = "SYNTHETIC"
    elif global_risk_score < THRESHOLD_REAL:
        verdict = "REAL"
    else:
        verdict = "SUSPICIOUS"
    
    # Calculate confidence based on sensor consensus
    # High confidence if sensors strongly agree
    confidence = calculate_confidence(contributing_factors, global_risk_score)
    
    # Sort contributing factors by contribution (descending)
    contributing_factors.sort(key=lambda x: x["contribution"], reverse=True)
    
    return {
        "global_risk_score": round(global_risk_score, 3),
        "verdict": verdict,
        "contributing_factors": contributing_factors,
        "confidence": round(confidence, 3),
        "metadata": {
            "total_sensors": len(results),
            "active_sensors": len(contributing_factors),
            "total_weight": round(total_weight, 3),
            "thresholds": {
                "synthetic": THRESHOLD_SYNTHETIC,
                "real": THRESHOLD_REAL
            }
        }
    }


def calculate_confidence(
    contributing_factors: List[Dict[str, Any]],
    global_risk_score: float
) -> float:
    """
    Calculate confidence level based on sensor consensus.
    
    High confidence occurs when:
    - Most sensors agree on direction (all high risk or all low risk)
    - The global score is far from the middle (0.5)
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not contributing_factors:
        return 0.0
    
    # Measure 1: Distance from middle (0.5)
    # Scores near 0 or 1 indicate high confidence
    distance_from_middle = abs(global_risk_score - 0.5) * 2  # Scale to 0-1
    
    # Measure 2: Variance in risk scores
    # Low variance means consensus
    risk_scores = [f["risk_score"] for f in contributing_factors]
    
    if len(risk_scores) == 0:
        return 0.0
    
    mean_risk = sum(risk_scores) / len(risk_scores)
    
    # Guard against division by zero in variance calculation
    if len(risk_scores) == 1:
        variance = 0.0  # Single sensor = no variance
    else:
        variance = sum((r - mean_risk) ** 2 for r in risk_scores) / len(risk_scores)
    
    consensus = 1.0 - min(variance, 1.0)  # Invert variance, cap at 1.0
    
    # Combine measures (weighted average)
    confidence = (distance_from_middle * 0.6) + (consensus * 0.4)
    
    return max(0.0, min(1.0, confidence))


def get_top_contributors(
    fusion_verdict: Dict[str, Any],
    top_n: int = 2
) -> List[Dict[str, Any]]:
    """
    Extract top N contributing sensors from fusion verdict.
    
    Args:
        fusion_verdict: Output from calculate_fusion_verdict
        top_n: Number of top contributors to return
        
    Returns:
        List of top contributing sensor details
    """
    factors = fusion_verdict.get("contributing_factors", [])
    return factors[:top_n]


def format_technical_evidence(fusion_verdict: Dict[str, Any]) -> str:
    """
    Format fusion verdict into human-readable technical evidence string.
    
    Used for SAR narrative generation.
    
    Args:
        fusion_verdict: Output from calculate_fusion_verdict
        
    Returns:
        Formatted technical evidence string
    """
    score = fusion_verdict.get("global_risk_score", 0.0)
    verdict = fusion_verdict.get("verdict", "UNKNOWN")
    top_factors = get_top_contributors(fusion_verdict, top_n=2)
    
    evidence = f"Global Risk Score: {score:.1%} ({verdict})\n\n"
    evidence += "Primary Contributing Factors:\n"
    
    for i, factor in enumerate(top_factors, 1):
        sensor = factor.get("sensor_name", "Unknown")
        contribution = factor.get("contribution", 0.0)
        reason = factor.get("reason") or factor.get("detail", "")
        
        evidence += f"{i}. {sensor} (Weight: {factor.get('weight', 0.0):.0%}, "
        evidence += f"Contribution: {contribution:.0%})\n"
        if reason:
            evidence += f"   Finding: {reason}\n"
    
    return evidence.strip()
