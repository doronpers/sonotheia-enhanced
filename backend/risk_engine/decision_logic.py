"""
Unified Decision Logic for Sonotheia

This module provides a centralized, consistent decision logic that should be used
across all components (calibration, API, fusion engine) to ensure consistent behavior.

Architecture:
1. PROSECUTION VETO: High-risk voice indicators trigger immediate escalation
2. DEFENSE VALIDATION: Consistently low risk across factors allows approval
3. COMPOSITE SCORING: Weighted combination with appropriate thresholds

This addresses the critical issue where deepfakes were being approved due to:
- Score dilution from 50/50 biometric/voice weighting
- ESCALATE threshold (0.5) being too high for diluted scores
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level categories"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Decision(str, Enum):
    """Authentication decisions"""
    APPROVE = "APPROVE"
    ESCALATE = "ESCALATE"
    DECLINE = "DECLINE"
    REVIEW = "REVIEW"


@dataclass
class DecisionThresholds:
    """
    Configurable decision thresholds.

    These values have been calibrated to balance:
    - High deepfake detection rate (minimize false negatives)
    - Acceptable false positive rate on legitimate users
    """
    # Voice risk thresholds
    voice_veto_threshold: float = 0.6      # Voice risk >= this triggers immediate ESCALATE
    voice_caution_threshold: float = 0.4   # Voice risk >= this requires extra scrutiny

    # Composite risk thresholds
    composite_low: float = 0.3             # Below this = LOW risk, APPROVE
    composite_medium: float = 0.5          # Below this = MEDIUM risk
    composite_high: float = 0.7            # Below this = HIGH risk
    # >= composite_high = CRITICAL risk

    # Factor weights (should sum to 1.0)
    biometric_weight: float = 0.3
    voice_weight: float = 0.7

    # Defense validation thresholds
    defense_trust_threshold: float = 0.3   # All factors below this = high trust


class UnifiedDecisionEngine:
    """
    Centralized decision engine for consistent authentication decisions.

    Usage:
        engine = UnifiedDecisionEngine()
        result = engine.make_decision(
            voice_risk=0.75,
            biometric_risk=0.1
        )
        # result.decision == Decision.ESCALATE
        # result.reason == "PROSECUTION_VETO"
    """

    def __init__(self, thresholds: Optional[DecisionThresholds] = None):
        """
        Initialize decision engine with configurable thresholds.

        Args:
            thresholds: Custom thresholds (uses defaults if None)
        """
        self.thresholds = thresholds or DecisionThresholds()
        logger.info(f"UnifiedDecisionEngine initialized with thresholds: "
                   f"voice_veto={self.thresholds.voice_veto_threshold}, "
                   f"composite_high={self.thresholds.composite_high}")

    def make_decision(
        self,
        voice_risk: float,
        biometric_risk: float = 0.0,
        additional_factors: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Make authentication decision based on risk factors.

        Args:
            voice_risk: Voice deepfake risk score (0.0-1.0)
            biometric_risk: Biometric verification risk (0.0-1.0)
            additional_factors: Optional additional risk factors

        Returns:
            Dict with decision, risk_level, composite_score, and reasoning
        """
        # Clamp inputs
        voice_risk = max(0.0, min(1.0, voice_risk))
        biometric_risk = max(0.0, min(1.0, biometric_risk))

        # Calculate composite risk
        composite_risk = (
            biometric_risk * self.thresholds.biometric_weight +
            voice_risk * self.thresholds.voice_weight
        )

        # Apply additional factors if provided
        if additional_factors:
            additional_weight = 0.0
            additional_sum = 0.0
            for factor_name, factor_score in additional_factors.items():
                factor_score = max(0.0, min(1.0, factor_score))
                additional_weight += 0.1  # Default weight for additional factors
                additional_sum += factor_score * 0.1

            # Renormalize
            total_weight = (self.thresholds.biometric_weight +
                          self.thresholds.voice_weight +
                          additional_weight)
            composite_risk = (
                biometric_risk * self.thresholds.biometric_weight +
                voice_risk * self.thresholds.voice_weight +
                additional_sum
            ) / total_weight

        # =====================================================
        # DECISION LOGIC
        # =====================================================

        decision: Decision
        risk_level: RiskLevel
        reason: str

        # Rule 1: PROSECUTION VETO
        # High voice risk triggers immediate escalation regardless of other factors
        if voice_risk >= self.thresholds.voice_veto_threshold:
            decision = Decision.ESCALATE
            risk_level = RiskLevel.CRITICAL if voice_risk >= 0.8 else RiskLevel.HIGH
            reason = "PROSECUTION_VETO"
            logger.warning(f"Prosecution veto triggered: voice_risk={voice_risk:.3f}")

        # Rule 2: CRITICAL composite risk
        elif composite_risk >= self.thresholds.composite_high:
            decision = Decision.ESCALATE
            risk_level = RiskLevel.CRITICAL
            reason = "CRITICAL_COMPOSITE_RISK"

        # Rule 3: HIGH composite risk
        elif composite_risk >= self.thresholds.composite_medium:
            decision = Decision.ESCALATE
            risk_level = RiskLevel.HIGH
            reason = "HIGH_COMPOSITE_RISK"

        # Rule 4: MEDIUM composite risk with voice caution
        elif composite_risk >= self.thresholds.composite_low:
            if voice_risk >= self.thresholds.voice_caution_threshold:
                # Voice risk is concerning even if composite is medium
                decision = Decision.ESCALATE
                risk_level = RiskLevel.MEDIUM
                reason = "VOICE_CAUTION_ESCALATE"
            else:
                decision = Decision.APPROVE
                risk_level = RiskLevel.MEDIUM
                reason = "MEDIUM_RISK_APPROVE"

        # Rule 5: LOW risk - Defense validation
        else:
            # Check if all factors indicate genuine user
            if (voice_risk < self.thresholds.defense_trust_threshold and
                biometric_risk < self.thresholds.defense_trust_threshold):
                decision = Decision.APPROVE
                risk_level = RiskLevel.LOW
                reason = "DEFENSE_VALIDATED"
            else:
                decision = Decision.APPROVE
                risk_level = RiskLevel.LOW
                reason = "LOW_RISK_APPROVE"

        return {
            "decision": decision.value,
            "risk_level": risk_level.value,
            "composite_risk": round(composite_risk, 4),
            "voice_risk": round(voice_risk, 4),
            "biometric_risk": round(biometric_risk, 4),
            "reason": reason,
            "prosecution_veto": voice_risk >= self.thresholds.voice_veto_threshold,
            "thresholds_used": {
                "voice_veto": self.thresholds.voice_veto_threshold,
                "voice_caution": self.thresholds.voice_caution_threshold,
                "composite_low": self.thresholds.composite_low,
                "composite_medium": self.thresholds.composite_medium,
                "composite_high": self.thresholds.composite_high,
            }
        }

    def make_decision_from_sensors(
        self,
        sensor_results: Dict[str, Dict[str, Any]],
        biometric_risk: float = 0.0
    ) -> Dict[str, Any]:
        """
        Make decision based on sensor results from physics analysis.

        This extracts voice_risk from sensor fusion and applies decision logic.

        Args:
            sensor_results: Results from sensor analysis pipeline
            biometric_risk: Optional biometric verification risk

        Returns:
            Decision result dict
        """
        # Extract voice risk from sensor results
        # Look for common keys that indicate deepfake probability
        voice_risk = 0.0

        # Try to get from fusion result
        if "global_risk_score" in sensor_results:
            voice_risk = sensor_results["global_risk_score"]
        elif "fused_score" in sensor_results:
            voice_risk = sensor_results["fused_score"]
        elif "physics_score" in sensor_results:
            voice_risk = sensor_results["physics_score"]
        else:
            # Calculate from individual sensors using max-of-prosecution
            prosecution_scores = []
            for name, result in sensor_results.items():
                if isinstance(result, dict):
                    score = result.get("score") or result.get("value", 0.0)
                    # Check if prosecution sensor
                    lower_name = name.lower()
                    if any(x in lower_name for x in ["glottal", "pitch", "silence", "two-mouth"]):
                        prosecution_scores.append(score)

            if prosecution_scores:
                voice_risk = max(prosecution_scores)

        return self.make_decision(
            voice_risk=voice_risk,
            biometric_risk=biometric_risk
        )

    @staticmethod
    def validate_thresholds(thresholds: DecisionThresholds) -> List[str]:
        """
        Validate that thresholds are internally consistent.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check threshold ordering
        if thresholds.composite_low >= thresholds.composite_medium:
            errors.append("composite_low must be < composite_medium")
        if thresholds.composite_medium >= thresholds.composite_high:
            errors.append("composite_medium must be < composite_high")

        # Check weights sum to 1.0
        weight_sum = thresholds.biometric_weight + thresholds.voice_weight
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"biometric_weight + voice_weight should equal 1.0, got {weight_sum}")

        # Check voice thresholds
        if thresholds.voice_caution_threshold >= thresholds.voice_veto_threshold:
            errors.append("voice_caution_threshold must be < voice_veto_threshold")

        # Check ranges
        for name, value in [
            ("voice_veto_threshold", thresholds.voice_veto_threshold),
            ("voice_caution_threshold", thresholds.voice_caution_threshold),
            ("composite_low", thresholds.composite_low),
            ("composite_medium", thresholds.composite_medium),
            ("composite_high", thresholds.composite_high),
        ]:
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name} must be between 0.0 and 1.0, got {value}")

        return errors


# Singleton instance with default thresholds
_default_engine: Optional[UnifiedDecisionEngine] = None


def get_decision_engine(thresholds: Optional[DecisionThresholds] = None) -> UnifiedDecisionEngine:
    """
    Get the unified decision engine instance.

    Args:
        thresholds: Custom thresholds (uses cached default if None)

    Returns:
        UnifiedDecisionEngine instance
    """
    global _default_engine

    if thresholds is not None:
        return UnifiedDecisionEngine(thresholds)

    if _default_engine is None:
        _default_engine = UnifiedDecisionEngine()

    return _default_engine


def make_decision(
    voice_risk: float,
    biometric_risk: float = 0.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for making decisions with default engine.

    Args:
        voice_risk: Voice deepfake risk score (0.0-1.0)
        biometric_risk: Biometric verification risk (0.0-1.0)
        **kwargs: Additional arguments passed to make_decision

    Returns:
        Decision result dict
    """
    return get_decision_engine().make_decision(
        voice_risk=voice_risk,
        biometric_risk=biometric_risk,
        **kwargs
    )
