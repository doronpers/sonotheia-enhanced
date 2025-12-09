"""
Tests for the unified decision logic.

Validates that:
1. High voice risk triggers prosecution veto (ESCALATE)
2. Legitimate users are approved (low false positive rate)
3. Deepfakes are escalated (high detection rate)
4. Edge cases are handled appropriately
"""

import pytest
from backend.risk_engine.decision_logic import (
    UnifiedDecisionEngine,
    DecisionThresholds,
    Decision,
    RiskLevel,
    make_decision,
    get_decision_engine,
)


class TestUnifiedDecisionEngine:
    """Test the unified decision engine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = UnifiedDecisionEngine()

    # =========================================================================
    # PROSECUTION VETO TESTS
    # =========================================================================

    def test_prosecution_veto_high_voice_risk(self):
        """High voice risk (>= 0.6) should trigger ESCALATE regardless of biometric"""
        result = self.engine.make_decision(voice_risk=0.75, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE"
        assert result["prosecution_veto"] is True
        assert result["reason"] == "PROSECUTION_VETO"

    def test_prosecution_veto_very_high_voice_risk(self):
        """Very high voice risk (>= 0.8) should be CRITICAL"""
        result = self.engine.make_decision(voice_risk=0.85, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE"
        assert result["risk_level"] == "CRITICAL"
        assert result["prosecution_veto"] is True

    def test_prosecution_veto_boundary(self):
        """Voice risk exactly at threshold should trigger veto"""
        result = self.engine.make_decision(voice_risk=0.6, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE"
        assert result["prosecution_veto"] is True

    def test_no_veto_below_threshold(self):
        """Voice risk below threshold should not trigger veto"""
        result = self.engine.make_decision(voice_risk=0.59, biometric_risk=0.0)

        assert result["prosecution_veto"] is False

    # =========================================================================
    # CALIBRATION DATA TESTS (from calibration_results_20251124_175133.json)
    # =========================================================================

    def test_calibration_deepfake_000(self):
        """
        CAL-SUSPICIOUS-000: voice_risk=0.994 should ESCALATE
        Previously: APPROVED (BUG)
        """
        result = self.engine.make_decision(voice_risk=0.994, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE", \
            f"Deepfake with voice_risk=0.994 should ESCALATE, got {result['decision']}"
        assert result["risk_level"] == "CRITICAL"

    def test_calibration_deepfake_001(self):
        """
        CAL-SUSPICIOUS-001: voice_risk=0.759 should ESCALATE
        Previously: APPROVED (BUG)
        """
        result = self.engine.make_decision(voice_risk=0.759, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE", \
            f"Deepfake with voice_risk=0.759 should ESCALATE, got {result['decision']}"

    def test_calibration_deepfake_002(self):
        """
        CAL-SUSPICIOUS-002: voice_risk=0.960 should ESCALATE
        Previously: APPROVED (BUG)
        """
        result = self.engine.make_decision(voice_risk=0.960, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE", \
            f"Deepfake with voice_risk=0.960 should ESCALATE, got {result['decision']}"

    def test_calibration_legitimate_users(self):
        """
        Legitimate users (voice_risk 0.05-0.25) should be APPROVED
        CAL-GOOD-000 through CAL-GOOD-008
        """
        legitimate_voice_risks = [0.17, 0.12, 0.20, 0.14, 0.16, 0.18, 0.20, 0.20, 0.20]

        for i, voice_risk in enumerate(legitimate_voice_risks):
            result = self.engine.make_decision(voice_risk=voice_risk, biometric_risk=0.0)
            assert result["decision"] == "APPROVE", \
                f"Legitimate user {i} with voice_risk={voice_risk} should APPROVE, got {result['decision']}"

    def test_calibration_edge_cases(self):
        """
        Edge cases (voice_risk 0.25-0.40) should be APPROVED
        CAL-EDGE-000, CAL-EDGE-001
        """
        edge_voice_risks = [0.35, 0.29]

        for i, voice_risk in enumerate(edge_voice_risks):
            result = self.engine.make_decision(voice_risk=voice_risk, biometric_risk=0.0)
            assert result["decision"] == "APPROVE", \
                f"Edge case {i} with voice_risk={voice_risk} should APPROVE, got {result['decision']}"

    # =========================================================================
    # THRESHOLD TESTS
    # =========================================================================

    def test_low_risk_approval(self):
        """Low risk (composite < 0.3) should approve"""
        result = self.engine.make_decision(voice_risk=0.1, biometric_risk=0.1)

        assert result["decision"] == "APPROVE"
        assert result["risk_level"] == "LOW"

    def test_medium_risk_with_low_voice(self):
        """Medium composite risk with low voice risk should approve"""
        # composite = 0.3 * 0.5 + 0.7 * 0.35 = 0.15 + 0.245 = 0.395
        result = self.engine.make_decision(voice_risk=0.35, biometric_risk=0.5)

        assert result["decision"] == "APPROVE"
        assert result["risk_level"] == "MEDIUM"

    def test_medium_risk_with_voice_caution(self):
        """Medium composite risk with voice >= caution threshold should escalate"""
        # Voice risk >= 0.4 in medium zone should escalate
        result = self.engine.make_decision(voice_risk=0.45, biometric_risk=0.3)

        assert result["decision"] == "ESCALATE"

    def test_high_composite_risk(self):
        """High composite risk should escalate"""
        # composite = 0.3 * 0.8 + 0.7 * 0.5 = 0.24 + 0.35 = 0.59
        result = self.engine.make_decision(voice_risk=0.5, biometric_risk=0.8)

        assert result["decision"] == "ESCALATE"
        assert result["risk_level"] == "HIGH"

    # =========================================================================
    # DEFENSE VALIDATION TESTS
    # =========================================================================

    def test_defense_validated_low_risk(self):
        """Very low risk on all factors should be defense validated"""
        result = self.engine.make_decision(voice_risk=0.1, biometric_risk=0.1)

        assert result["decision"] == "APPROVE"
        assert result["reason"] == "DEFENSE_VALIDATED"

    # =========================================================================
    # CUSTOM THRESHOLD TESTS
    # =========================================================================

    def test_custom_thresholds(self):
        """Custom thresholds should be applied"""
        custom = DecisionThresholds(
            voice_veto_threshold=0.5,  # Stricter
            composite_high=0.6,
        )
        engine = UnifiedDecisionEngine(thresholds=custom)

        result = engine.make_decision(voice_risk=0.55, biometric_risk=0.0)

        assert result["decision"] == "ESCALATE"
        assert result["prosecution_veto"] is True

    def test_threshold_validation(self):
        """Invalid thresholds should be detected"""
        invalid = DecisionThresholds(
            composite_low=0.7,   # Invalid: should be < composite_medium
            composite_medium=0.5,
            composite_high=0.9,
        )

        errors = UnifiedDecisionEngine.validate_thresholds(invalid)
        assert len(errors) > 0
        assert any("composite_low must be < composite_medium" in e for e in errors)

    # =========================================================================
    # CONVENIENCE FUNCTION TESTS
    # =========================================================================

    def test_convenience_function(self):
        """make_decision convenience function should work"""
        result = make_decision(voice_risk=0.8)

        assert result["decision"] == "ESCALATE"

    def test_singleton_engine(self):
        """get_decision_engine should return cached instance"""
        engine1 = get_decision_engine()
        engine2 = get_decision_engine()

        assert engine1 is engine2


class TestDecisionLogicWithRealData:
    """
    Tests using the actual calibration data to verify
    the fix resolves the 0% deepfake detection rate.
    """

    def test_all_deepfakes_escalated(self):
        """ALL deepfakes from calibration should be ESCALATED"""
        engine = UnifiedDecisionEngine()

        # Actual deepfake_scores from calibration data
        deepfakes = [
            {"id": "CAL-SUSPICIOUS-000", "deepfake_score": 0.45, "speaker_verified": False, "speaker_score": 0.60},
            {"id": "CAL-SUSPICIOUS-001", "deepfake_score": 0.60, "speaker_verified": False, "speaker_score": 0.70},
            {"id": "CAL-SUSPICIOUS-002", "deepfake_score": 0.85, "speaker_verified": False, "speaker_score": 0.65},
        ]

        for df in deepfakes:
            # Calculate voice_risk as in calibration tool
            voice_risk = df["deepfake_score"]
            if not df["speaker_verified"]:
                voice_risk += 0.2
            if df["speaker_score"] < 0.8:
                voice_risk += (1.0 - df["speaker_score"]) * 0.2
            voice_risk = min(voice_risk, 1.0)

            result = engine.make_decision(voice_risk=voice_risk, biometric_risk=0.0)

            assert result["decision"] == "ESCALATE", \
                f"{df['id']} with calculated voice_risk={voice_risk:.3f} should ESCALATE, got {result['decision']}"

    def test_all_legitimate_approved(self):
        """ALL legitimate users from calibration should be APPROVED"""
        engine = UnifiedDecisionEngine()

        # Actual legitimate user data from calibration
        legitimate = [
            {"id": "CAL-GOOD-000", "deepfake_score": 0.15, "speaker_verified": True, "speaker_score": 0.92},
            {"id": "CAL-GOOD-001", "deepfake_score": 0.08, "speaker_verified": True, "speaker_score": 0.95},
            {"id": "CAL-GOOD-002", "deepfake_score": 0.18, "speaker_verified": True, "speaker_score": 0.90},
        ]

        for user in legitimate:
            # Calculate voice_risk as in calibration tool
            voice_risk = user["deepfake_score"]
            if not user["speaker_verified"]:
                voice_risk += 0.2
            if user["speaker_score"] < 0.8:
                voice_risk += (1.0 - user["speaker_score"]) * 0.2
            voice_risk = min(voice_risk, 1.0)

            result = engine.make_decision(voice_risk=voice_risk, biometric_risk=0.0)

            assert result["decision"] == "APPROVE", \
                f"{user['id']} with voice_risk={voice_risk:.3f} should APPROVE, got {result['decision']}"

    def test_detection_rate_improvement(self):
        """
        Verify the decision logic improves deepfake detection rate from 0% to 100%
        """
        engine = UnifiedDecisionEngine()

        # Test data representing the calibration scenarios
        test_cases = [
            # (voice_risk, expected_decision, description)
            (0.994, "ESCALATE", "High confidence deepfake"),
            (0.759, "ESCALATE", "Medium-high deepfake"),
            (0.960, "ESCALATE", "High confidence deepfake"),
            (0.17, "APPROVE", "Legitimate user"),
            (0.12, "APPROVE", "Legitimate user"),
            (0.35, "APPROVE", "Edge case legitimate"),
        ]

        correct = 0
        total = len(test_cases)

        for voice_risk, expected, description in test_cases:
            result = engine.make_decision(voice_risk=voice_risk, biometric_risk=0.0)
            if result["decision"] == expected:
                correct += 1
            else:
                print(f"FAILED: {description} (voice_risk={voice_risk}) "
                      f"expected {expected}, got {result['decision']}")

        accuracy = correct / total
        assert accuracy >= 1.0, f"Expected 100% accuracy, got {accuracy*100:.1f}%"
