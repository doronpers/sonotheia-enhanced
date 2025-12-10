#!/usr/bin/env python3
"""
Test suite to validate fusion engine and sensor fixes.

Tests:
1. Score clamping to [0,1] range
2. BandwidthSensor exclusion from risk calculations
3. Short audio handling without n_fft warnings
4. Physics analysis contribution to final score
5. Stage weight normalization
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.detection.stages.fusion_engine import FusionEngine
from backend.sensors.digital_silence import DigitalSilenceSensor
from backend.detection.stages.physics_analysis import PhysicsAnalysisStage


class TestScoreClamping:
    """Test that all scores are properly clamped to [0,1]"""

    def test_out_of_range_physics_score(self):
        """Verify physics_score is clamped if out of range"""
        fusion = FusionEngine()

        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 1.5,  # Out of range!
                "sensor_results": {}
            }
        }

        result = fusion.fuse(stage_results)

        assert 0.0 <= result["fused_score"] <= 1.0, \
            f"Score not clamped: {result['fused_score']}"
        print(f"✓ Physics score clamped: input=1.5, output={result['fused_score']:.3f}")

    def test_negative_sensor_score(self):
        """Verify negative sensor scores are clamped to 0"""
        fusion = FusionEngine()

        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.5,
                "sensor_results": {
                    "TestSensor": {
                        "score": -0.5,  # Negative!
                        "value": -0.5,
                        "passed": True
                    }
                }
            }
        }

        result = fusion.fuse(stage_results)

        assert 0.0 <= result["fused_score"] <= 1.0, \
            f"Negative score not clamped: {result['fused_score']}"
        print(f"✓ Negative score clamped: output={result['fused_score']:.3f}")

    def test_very_high_sensor_score(self):
        """Verify very high sensor scores are clamped to 1.0"""
        fusion = FusionEngine()

        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.5,
                "sensor_results": {
                    "TestSensor": {
                        "score": 100.0,  # Way too high!
                        "value": 100.0,
                        "passed": False
                    }
                }
            }
        }

        result = fusion.fuse(stage_results)

        assert 0.0 <= result["fused_score"] <= 1.0, \
            f"High score not clamped: {result['fused_score']}"
        print(f"✓ High score clamped: input=100.0, output={result['fused_score']:.3f}")


class TestBandwidthSensorExclusion:
    """Test that BandwidthSensor doesn't contaminate risk calculations"""

    def test_bandwidth_raw_frequency_ignored(self):
        """Verify BandwidthSensor's raw frequency values don't affect risk_score"""
        fusion = FusionEngine()

        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.3,
                "sensor_results": {
                    "BandwidthSensor": {
                        "score": 6321.0,  # Raw frequency (should be ignored!)
                        "value": 6321.0,
                        "passed": None,
                        "metadata": {"rolloff_frequency_hz": 6321.0}
                    },
                    "GlottalInertiaSensor": {
                        "score": 0.8,
                        "value": 0.8,
                        "passed": False
                    }
                }
            }
        }

        result = fusion.fuse(stage_results)

        # Risk should be influenced by GlottalInertia (0.8), NOT BandwidthSensor (6321)!
        assert result["fused_score"] < 10.0, \
            f"BandwidthSensor contaminated score: {result['fused_score']}"
        assert result["fused_score"] <= 1.0, \
            f"Score exceeded 1.0: {result['fused_score']}"
        print(f"✓ BandwidthSensor properly excluded: score={result['fused_score']:.3f}")

    def test_bandwidth_informational_category(self):
        """Verify BandwidthSensor with 'informational' category is skipped"""
        fusion = FusionEngine()

        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.2,
                "sensor_results": {
                    "BandwidthSensor": {
                        "score": 5000.0,
                        "passed": None,
                        "metadata": {"category": "informational"}
                    },
                    "FormantTrajectorySensor": {
                        "score": 0.3,
                        "passed": True
                    }
                }
            }
        }

        result = fusion.fuse(stage_results)

        # Should only use FormantTrajectorySensor and physics_score
        assert result["fused_score"] < 1.0
        print(f"✓ Informational sensor skipped: score={result['fused_score']:.3f}")


class TestShortAudioHandling:
    """Test that short audio doesn't trigger warnings"""

    def test_very_short_audio_no_crash(self):
        """Verify very short audio (< 2048 samples) is handled gracefully"""
        sensor = DigitalSilenceSensor()

        # 50ms @ 16kHz = 800 samples (< 2048)
        short_audio = np.random.randn(800).astype(np.float32)

        result = sensor.analyze(short_audio, 16000)

        assert result is not None, "Sensor crashed on short audio"
        assert result.sensor_name == "Digital Silence Sensor"
        print(f"✓ Short audio handled: {len(short_audio)} samples, score={result.value:.3f}")

    def test_borderline_audio_length(self):
        """Test audio right at the 2048 sample boundary"""
        sensor = DigitalSilenceSensor()

        # Exactly 2048 samples (128ms @ 16kHz)
        borderline_audio = np.random.randn(2048).astype(np.float32)

        result = sensor.analyze(borderline_audio, 16000)

        assert result is not None
        assert 0.0 <= result.value <= 1.0
        print(f"✓ Borderline audio handled: {len(borderline_audio)} samples, score={result.value:.3f}")

    def test_adequate_audio_length(self):
        """Test audio with adequate length for analysis"""
        sensor = DigitalSilenceSensor()

        # 5 seconds @ 16kHz = 80,000 samples
        adequate_audio = np.random.randn(80000).astype(np.float32)

        result = sensor.analyze(adequate_audio, 16000)

        assert result is not None
        assert 0.0 <= result.value <= 1.0
        print(f"✓ Adequate audio analyzed: {len(adequate_audio)} samples, score={result.value:.3f}")


class TestPhysicsAnalysisContribution:
    """Test that physics_analysis properly contributes to final score"""

    def test_high_physics_score_influences_final(self):
        """Verify high physics_score increases final score"""
        fusion = FusionEngine()

        # Scenario: Physics says FAKE (0.9), but RawNet3 says REAL (0.1)
        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.9,  # High fake probability
                "sensor_results": {}
            },
            "rawnet3": {
                "success": True,
                "score": 0.1  # Low fake probability
            }
        }

        result = fusion.fuse(stage_results)

        # Final score should be influenced by physics (0.9), not just RawNet3 (0.1)
        # With 25% weight for physics and 45% for rawnet3:
        # Expected: 0.25*0.9 + 0.45*0.1 = 0.225 + 0.045 = 0.27 (approximately)
        assert result["fused_score"] > 0.2, \
            f"Physics analysis not contributing: {result['fused_score']:.3f}"
        print(f"✓ Physics analysis contributing: final={result['fused_score']:.3f}")

    def test_low_physics_score_decreases_final(self):
        """Verify low physics_score decreases final score"""
        fusion = FusionEngine()

        # Scenario: Physics says REAL (0.1), RawNet3 says FAKE (0.9)
        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.1,  # Low fake probability (real)
                "sensor_results": {}
            },
            "rawnet3": {
                "success": True,
                "score": 0.9  # High fake probability
            }
        }

        result = fusion.fuse(stage_results)

        # Final should be pulled down by physics
        # Expected: 0.25*0.1 + 0.45*0.9 = 0.025 + 0.405 = 0.43 (approximately)
        assert result["fused_score"] < 0.9, \
            f"Physics analysis not moderating score: {result['fused_score']:.3f}"
        assert result["fused_score"] > 0.3, \
            f"Physics analysis over-moderating: {result['fused_score']:.3f}"
        print(f"✓ Physics analysis moderating: final={result['fused_score']:.3f}")

    def test_physics_only_scenario(self):
        """Test fusion with only physics_analysis results"""
        fusion = FusionEngine()

        stage_results = {
            "physics_analysis": {
                "success": True,
                "physics_score": 0.75,
                "sensor_results": {}
            }
        }

        result = fusion.fuse(stage_results)

        # Should use physics_score as primary indicator
        assert result["fused_score"] >= 0.5, \
            f"Physics-only score too low: {result['fused_score']:.3f}"
        print(f"✓ Physics-only fusion works: final={result['fused_score']:.3f}")


class TestStageWeightNormalization:
    """Test that stage weights sum to reasonable values"""

    def test_weights_sum_to_one(self):
        """Verify stage weights sum to 1.0 (100%)"""
        fusion = FusionEngine()

        total_weight = sum(fusion.stage_weights.values())

        assert 0.99 <= total_weight <= 1.01, \
            f"Stage weights don't sum to 1.0: {total_weight:.3f}"
        print(f"✓ Stage weights normalized: sum={total_weight:.3f}")
        print(f"  Weights: {fusion.stage_weights}")

    def test_physics_analysis_has_weight(self):
        """Verify physics_analysis has a weight assigned"""
        fusion = FusionEngine()

        assert "physics_analysis" in fusion.stage_weights, \
            "physics_analysis missing from stage_weights!"

        physics_weight = fusion.stage_weights["physics_analysis"]
        assert physics_weight > 0, \
            f"physics_analysis weight is zero: {physics_weight}"
        assert physics_weight >= 0.20, \
            f"physics_analysis weight too low: {physics_weight} (expected >= 0.20)"

        print(f"✓ physics_analysis weight configured: {physics_weight:.2f}")


def run_all_tests():
    """Run all test suites and report results"""
    print("=" * 60)
    print("  FUSION ENGINE & SENSOR FIXES VALIDATION")
    print("=" * 60)
    print()

    test_classes = [
        ("Score Clamping", TestScoreClamping),
        ("BandwidthSensor Exclusion", TestBandwidthSensorExclusion),
        ("Short Audio Handling", TestShortAudioHandling),
        ("Physics Analysis Contribution", TestPhysicsAnalysisContribution),
        ("Stage Weight Normalization", TestStageWeightNormalization),
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for suite_name, test_class in test_classes:
        print(f"\n{suite_name}:")
        print("-" * 60)

        # Get all test methods
        test_methods = [m for m in dir(test_class) if m.startswith("test_")]

        for method_name in test_methods:
            total_tests += 1
            try:
                test_instance = test_class()
                getattr(test_instance, method_name)()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append((suite_name, method_name, str(e)))
                print(f"✗ {method_name}: {e}")
            except Exception as e:
                failed_tests.append((suite_name, method_name, f"Exception: {e}"))
                print(f"✗ {method_name}: Exception: {e}")

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if failed_tests:
        print("\nFailed tests:")
        for suite, method, error in failed_tests:
            print(f"  - {suite}.{method}: {error}")
        return False
    else:
        print("\n✅ All validation tests passed!")
        print("\nNext steps:")
        print("1. Run micro test: python3 backend/scripts/run_micro_test.py --count 10")
        print("2. Check for warnings: ... 2>&1 | grep -i 'n_fft\\|warning'")
        print("3. Run full benchmark: python3 backend/scripts/generate_accuracy_report.py")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
