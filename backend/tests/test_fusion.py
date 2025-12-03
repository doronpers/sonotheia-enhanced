"""
Tests for Multi-Sensor Fusion Engine
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from sensors.base import SensorResult
from sensors.fusion import (
    calculate_fusion_verdict,
    calculate_confidence,
    get_top_contributors,
    format_technical_evidence,
    DEFAULT_WEIGHTS,
)


def test_fusion_verdict_all_pass():
    """Test fusion when all sensors pass (real audio)"""
    results = [
        SensorResult("BreathSensor", passed=True, value=0.1, threshold=0.5),
        SensorResult("BandwidthSensor", passed=True, value=0.2, threshold=0.5),
        SensorResult("PhaseCoherenceSensor", passed=True, value=0.3, threshold=0.5),
    ]
    
    verdict = calculate_fusion_verdict(results)
    
    assert verdict["global_risk_score"] < 0.3
    assert verdict["verdict"] == "REAL"
    assert verdict["confidence"] > 0.5
    assert len(verdict["contributing_factors"]) == 3


def test_fusion_verdict_all_fail():
    """Test fusion when all sensors fail (synthetic audio)"""
    results = [
        SensorResult("BreathSensor", passed=False, value=0.9, threshold=0.5),
        SensorResult("BandwidthSensor", passed=False, value=0.8, threshold=0.5),
        SensorResult("PhaseCoherenceSensor", passed=False, value=0.7, threshold=0.5),
    ]
    
    verdict = calculate_fusion_verdict(results)
    
    assert verdict["global_risk_score"] > 0.7
    assert verdict["verdict"] == "SYNTHETIC"
    assert verdict["confidence"] > 0.5


def test_fusion_verdict_mixed():
    """Test fusion with mixed sensor results (suspicious)"""
    results = [
        SensorResult("BreathSensor", passed=True, value=0.3, threshold=0.5),
        SensorResult("BandwidthSensor", passed=False, value=0.7, threshold=0.5),
        SensorResult("PhaseCoherenceSensor", passed=True, value=0.4, threshold=0.5),
    ]
    
    verdict = calculate_fusion_verdict(results)
    
    assert 0.3 <= verdict["global_risk_score"] <= 0.7
    assert verdict["verdict"] == "SUSPICIOUS"


def test_fusion_verdict_with_skipped_sensors():
    """Test fusion when some sensors are skipped (passed=None)"""
    results = [
        SensorResult("BreathSensor", passed=False, value=0.8, threshold=0.5),
        SensorResult("HuggingFaceDetector", passed=None, value=0.0, threshold=0.5, 
                    reason="Skipped: API key missing"),
        SensorResult("PhaseCoherenceSensor", passed=False, value=0.7, threshold=0.5),
    ]
    
    verdict = calculate_fusion_verdict(results)
    
    # Should only count 2 active sensors
    assert verdict["metadata"]["active_sensors"] == 2
    assert verdict["metadata"]["total_sensors"] == 3
    assert verdict["verdict"] == "SYNTHETIC"


def test_fusion_verdict_custom_weights():
    """Test fusion with custom weight configuration"""
    results = [
        SensorResult("BreathSensor", passed=False, value=0.8, threshold=0.5),
        SensorResult("BandwidthSensor", passed=True, value=0.2, threshold=0.5),
    ]
    
    custom_weights = {
        "BreathSensor": 0.8,  # Much higher weight
        "BandwidthSensor": 0.2,
    }
    
    verdict = calculate_fusion_verdict(results, weights=custom_weights)
    
    # With 80% weight on failed breath sensor, should be SYNTHETIC
    assert verdict["verdict"] == "SYNTHETIC"
    assert verdict["global_risk_score"] > 0.7


def test_fusion_verdict_empty_results():
    """Test fusion with no sensor results"""
    verdict = calculate_fusion_verdict([])
    
    assert verdict["verdict"] == "UNKNOWN"
    assert verdict["global_risk_score"] == 0.5
    assert "error" in verdict["metadata"]


def test_calculate_confidence_high():
    """Test confidence calculation with strong consensus"""
    factors = [
        {"risk_score": 1.0, "contribution": 0.3},
        {"risk_score": 1.0, "contribution": 0.25},
        {"risk_score": 1.0, "contribution": 0.25},
    ]
    
    confidence = calculate_confidence(factors, global_risk_score=1.0)
    assert confidence > 0.7


def test_calculate_confidence_low():
    """Test confidence calculation with disagreement"""
    factors = [
        {"risk_score": 1.0, "contribution": 0.3},
        {"risk_score": 0.0, "contribution": 0.25},
        {"risk_score": 1.0, "contribution": 0.25},
    ]
    
    confidence = calculate_confidence(factors, global_risk_score=0.5)
    assert confidence < 0.5


def test_get_top_contributors():
    """Test extracting top contributing sensors"""
    verdict = {
        "contributing_factors": [
            {"sensor_name": "BreathSensor", "contribution": 0.3},
            {"sensor_name": "BandwidthSensor", "contribution": 0.25},
            {"sensor_name": "PhaseCoherenceSensor", "contribution": 0.1},
        ]
    }
    
    top_2 = get_top_contributors(verdict, top_n=2)
    
    assert len(top_2) == 2
    assert top_2[0]["sensor_name"] == "BreathSensor"
    assert top_2[1]["sensor_name"] == "BandwidthSensor"


def test_format_technical_evidence():
    """Test formatting fusion verdict for SAR narrative"""
    results = [
        SensorResult("BreathSensor", passed=False, value=0.8, threshold=0.5,
                    reason="No respiratory artifacts detected"),
        SensorResult("PhaseCoherenceSensor", passed=False, value=0.7, threshold=0.5,
                    reason="Abnormal phase coherence pattern"),
    ]
    
    verdict = calculate_fusion_verdict(results)
    evidence = format_technical_evidence(verdict)
    
    assert "Global Risk Score" in evidence
    assert "BreathSensor" in evidence
    assert "Primary Contributing Factors" in evidence


def test_weighted_scoring_accuracy():
    """Test that weights are applied correctly"""
    # Create scenario where high-weight sensor should dominate
    results = [
        SensorResult("BreathSensor", passed=False, value=0.9, threshold=0.5),  # 0.3 weight
        SensorResult("PhaseCoherenceSensor", passed=True, value=0.1, threshold=0.5),  # 0.1 weight
    ]
    
    verdict = calculate_fusion_verdict(results)
    
    # Expected: (1.0 * 0.3 + 0.0 * 0.1) / (0.3 + 0.1) = 0.75
    assert abs(verdict["global_risk_score"] - 0.75) < 0.01
    assert verdict["verdict"] == "SYNTHETIC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
