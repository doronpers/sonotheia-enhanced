"""
Factor-Level Risk Engine

Implements factor-based risk scoring for the Sonotheia MVP.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FactorType(str, Enum):
    """Types of authentication factors"""
    PHYSICS_DEEPFAKE = "physics_deepfake"
    ASV = "asv"
    LIVENESS = "liveness"
    DEVICE = "device"
    BEHAVIORAL = "behavioral"
    TRANSACTION = "transaction"


class FactorScore(BaseModel):
    """Individual factor score"""
    name: str = Field(..., description="Factor name (e.g., 'physics_deepfake', 'asv', 'liveness')")
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score 0-1, where higher = more risk")
    weight: float = Field(default=1.0, ge=0.0, description="Weight for this factor")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in this score")
    explanation: str = Field(..., description="Human-readable explanation")
    evidence: Optional[Dict[str, Any]] = Field(default=None, description="Supporting evidence data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "physics_deepfake",
                "score": 0.25,
                "weight": 2.0,
                "confidence": 0.95,
                "explanation": "Physics-based codec analysis indicates 25% likelihood of synthetic or manipulated audio.",
                "evidence": {
                    "codec_tested": "landline",
                    "raw_score": 0.25,
                    "threshold": 0.30
                }
            }
        }
    )


class RiskResult(BaseModel):
    """Overall risk result with factor breakdown"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score 0-1")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")
    factors: List[FactorScore] = Field(..., description="Individual factor scores")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata (call_id, codecs, etc.)")
    decision: str = Field(default="REVIEW", description="Recommended decision: APPROVE, DECLINE, REVIEW")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_score": 0.28,
                "risk_level": "LOW",
                "factors": [
                    {
                        "name": "physics_deepfake",
                        "score": 0.25,
                        "weight": 2.0,
                        "confidence": 0.95,
                        "explanation": "Physics-based codec analysis indicates low likelihood of synthetic audio."
                    }
                ],
                "meta": {
                    "call_id": "CALL-001",
                    "codecs_applied": ["landline"]
                },
                "decision": "APPROVE"
            }
        }
    )


class RiskEngine:
    """Compute overall risk from multiple factors"""

    # Risk level thresholds
    THRESHOLDS = {
        'LOW': 0.3,
        'MEDIUM': 0.5,
        'HIGH': 0.7,
        'CRITICAL': 0.85
    }

    @staticmethod
    def compute_overall_risk(factors: List[FactorScore]) -> RiskResult:
        """
        Compute overall risk from factors

        Args:
            factors: List of factor scores

        Returns:
            RiskResult with overall score and risk level
        """
        if not factors:
            raise ValueError("Cannot compute risk with no factors")

        # Weighted average of factor scores
        total_weight = sum(f.weight * f.confidence for f in factors)

        if total_weight == 0:
            overall_score = 0.5  # Neutral if no weighted factors
        else:
            weighted_sum = sum(f.score * f.weight * f.confidence for f in factors)
            overall_score = weighted_sum / total_weight

        # Determine risk level
        risk_level = RiskEngine._get_risk_level(overall_score)

        # Determine decision
        decision = RiskEngine._make_decision(overall_score, risk_level)

        result = RiskResult(
            overall_score=overall_score,
            risk_level=risk_level,
            factors=factors,
            decision=decision
        )

        logger.info(f"Computed risk: overall={overall_score:.3f}, level={risk_level}, decision={decision}")

        return result

    @staticmethod
    def _get_risk_level(score: float) -> str:
        """Determine risk level from score"""
        if score >= RiskEngine.THRESHOLDS['CRITICAL']:
            return 'CRITICAL'
        elif score >= RiskEngine.THRESHOLDS['HIGH']:
            return 'HIGH'
        elif score >= RiskEngine.THRESHOLDS['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'LOW'

    @staticmethod
    def _make_decision(score: float, risk_level: str) -> str:
        """Make decision based on risk level"""
        if risk_level == 'CRITICAL' or risk_level == 'HIGH':
            return 'DECLINE'
        elif risk_level == 'MEDIUM':
            return 'REVIEW'
        else:
            return 'APPROVE'

    @staticmethod
    def create_physics_factor(
        spoof_score: float,
        codec_name: str = "unknown",
        threshold: float = 0.30,
        weight: float = 2.0
    ) -> FactorScore:
        """
        Create physics-based deepfake factor from spoof detection score

        Args:
            spoof_score: Spoof probability from model (0-1)
            codec_name: Name of codec applied
            threshold: Detection threshold
            weight: Factor weight

        Returns:
            FactorScore for physics detection
        """
        # Generate explanation
        if spoof_score < threshold:
            explanation = (
                f"Physics-based codec analysis indicates {spoof_score*100:.1f}% likelihood "
                f"of synthetic or manipulated audio (tested with {codec_name} codec). "
                f"Score is below threshold ({threshold}), suggesting genuine audio."
            )
        else:
            explanation = (
                f"Physics-based codec analysis indicates {spoof_score*100:.1f}% likelihood "
                f"of synthetic or manipulated audio (tested with {codec_name} codec). "
                f"Score exceeds threshold ({threshold}), indicating potential deepfake."
            )

        return FactorScore(
            name="physics_deepfake",
            score=spoof_score,
            weight=weight,
            confidence=0.95,  # High confidence in physics-based detection
            explanation=explanation,
            evidence={
                "codec_tested": codec_name,
                "raw_score": spoof_score,
                "threshold": threshold
            }
        )

    @staticmethod
    def create_asv_factor(score: float = 0.15, weight: float = 1.5) -> FactorScore:
        """
        Create placeholder ASV (speaker verification) factor

        Args:
            score: Risk score (0-1)
            weight: Factor weight

        Returns:
            FactorScore for ASV
        """
        return FactorScore(
            name="asv",
            score=score,
            weight=weight,
            confidence=0.85,
            explanation=(
                f"Speaker verification check shows {(1-score)*100:.1f}% match "
                f"with enrolled voiceprint. Risk score: {score*100:.1f}%."
            ),
            evidence={"placeholder": True}
        )

    @staticmethod
    def create_liveness_factor(score: float = 0.10, weight: float = 1.5) -> FactorScore:
        """
        Create placeholder liveness factor

        Args:
            score: Risk score (0-1)
            weight: Factor weight

        Returns:
            FactorScore for liveness
        """
        return FactorScore(
            name="liveness",
            score=score,
            weight=weight,
            confidence=0.80,
            explanation=(
                f"Liveness detection indicates {(1-score)*100:.1f}% probability "
                f"of live human speech. Risk score: {score*100:.1f}%."
            ),
            evidence={"placeholder": True}
        )

    @staticmethod
    def create_device_factor(score: float = 0.20, weight: float = 1.0) -> FactorScore:
        """
        Create placeholder device trust factor

        Args:
            score: Risk score (0-1)
            weight: Factor weight

        Returns:
            FactorScore for device trust
        """
        return FactorScore(
            name="device",
            score=score,
            weight=weight,
            confidence=0.90,
            explanation=(
                f"Device trust score: {(1-score)*100:.1f}%. "
                f"Device validation indicates {score*100:.1f}% risk."
            ),
            evidence={"placeholder": True}
        )
