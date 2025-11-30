"""
Stage 5: Dual-Branch Fusion Engine

Combines results from multiple detection stages into a final score.
"""

import logging
from typing import Dict, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FusionEngine:
    """
    Stage 5: Dual-Branch Fusion

    Fuses scores from multiple detection stages:
    - Weighted average fusion
    - Maximum score fusion
    - Learned fusion (placeholder)
    """

    def __init__(
        self,
        fusion_method: str = "weighted_average",
        stage_weights: Optional[Dict[str, float]] = None,
        confidence_threshold: float = 0.5,
        decision_threshold: float = 0.5,
    ):
        """
        Initialize fusion engine.

        Args:
            fusion_method: Fusion method ("weighted_average", "max", "learned")
            stage_weights: Weights for each stage
            confidence_threshold: Minimum confidence for inclusion
            decision_threshold: Threshold for spoof decision
        """
        self.fusion_method = fusion_method
        self.stage_weights = stage_weights or {
            "feature_extraction": 0.15,
            "temporal_analysis": 0.15,
            "artifact_detection": 0.15,
            "rawnet3": 0.40,
            "explainability": 0.15,
        }
        self.confidence_threshold = confidence_threshold
        self.decision_threshold = decision_threshold

        logger.info(f"FusionEngine initialized: method={fusion_method}")

    def fuse(self, stage_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fuse results from multiple stages.

        Args:
            stage_results: Dictionary of stage name -> stage result

        Returns:
            Fused detection result
        """
        if not stage_results:
            return self._empty_result("No stage results to fuse")

        try:
            # Extract scores from each stage
            scores = self._extract_scores(stage_results)

            if not scores:
                return self._empty_result("No valid scores to fuse")

            # Apply fusion method
            if self.fusion_method == "weighted_average":
                fused_score = self._weighted_average_fusion(scores)
            elif self.fusion_method == "max":
                fused_score = self._max_fusion(scores)
            elif self.fusion_method == "learned":
                fused_score = self._learned_fusion(scores)
            else:
                fused_score = self._weighted_average_fusion(scores)

            # Compute overall confidence
            confidence = self._compute_confidence(stage_results, scores)

            # Make decision
            is_spoof = fused_score > self.decision_threshold
            decision = self._make_decision(fused_score, confidence)

            return {
                "success": True,
                "fused_score": float(fused_score),
                "confidence": float(confidence),
                "is_spoof": is_spoof,
                "decision": decision,
                "stage_scores": scores,
                "fusion_method": self.fusion_method,
                "stage_contributions": self._compute_contributions(scores, fused_score),
            }

        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            return self._empty_result(str(e))

    def _extract_scores(self, stage_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Extract scores from stage results."""
        scores = {}

        for stage_name, result in stage_results.items():
            if not result.get("success", False):
                continue

            # Get score based on stage type
            score = None
            if "score" in result:
                score = result["score"]
            elif "anomaly_score" in result:
                score = result["anomaly_score"]
            elif "temporal_score" in result:
                score = result["temporal_score"]
            elif "artifact_score" in result:
                score = result["artifact_score"]

            if score is not None:
                scores[stage_name] = float(score)

        return scores

    def _weighted_average_fusion(self, scores: Dict[str, float]) -> float:
        """Compute weighted average of scores."""
        total_weight = 0.0
        weighted_sum = 0.0

        for stage_name, score in scores.items():
            weight = self.stage_weights.get(stage_name, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.5

        return weighted_sum / total_weight

    def _max_fusion(self, scores: Dict[str, float]) -> float:
        """Return maximum score across stages."""
        if not scores:
            return 0.5
        return max(scores.values())

    def _learned_fusion(self, scores: Dict[str, float]) -> float:
        """
        Learned fusion (placeholder).

        In production, this would use a trained model to combine scores.
        """
        # For now, fall back to weighted average
        logger.warning("Learned fusion not implemented, using weighted average")
        return self._weighted_average_fusion(scores)

    def _compute_confidence(
        self, stage_results: Dict[str, Dict[str, Any]], scores: Dict[str, float]
    ) -> float:
        """Compute overall confidence in the result."""
        confidences = []

        for stage_name, result in stage_results.items():
            if stage_name in scores:
                # Get stage confidence if available
                stage_conf = result.get("confidence", 0.8)
                confidences.append(stage_conf)

        if not confidences:
            return 0.5

        # Average confidence, weighted by stage importance
        return float(np.mean(confidences))

    def _make_decision(self, score: float, confidence: float) -> str:
        """Make decision based on score and confidence."""
        if confidence < self.confidence_threshold:
            return "UNCERTAIN"

        if score > 0.7:
            return "SPOOF_HIGH"
        elif score > self.decision_threshold:
            return "SPOOF_LIKELY"
        elif score > 0.3:
            return "UNCERTAIN"
        else:
            return "GENUINE_LIKELY"

    def _compute_contributions(
        self, scores: Dict[str, float], fused_score: float
    ) -> Dict[str, float]:
        """Compute each stage's contribution to final score."""
        contributions = {}

        total_contribution = 0.0
        for stage_name, score in scores.items():
            weight = self.stage_weights.get(stage_name, 0.1)
            contribution = score * weight
            contributions[stage_name] = float(contribution)
            total_contribution += contribution

        # Normalize contributions
        if total_contribution > 0:
            for stage_name in contributions:
                contributions[stage_name] /= total_contribution

        return contributions

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed fusion."""
        return {
            "success": False,
            "error": error_msg,
            "fused_score": 0.5,
            "confidence": 0.0,
            "is_spoof": False,
            "decision": "UNCERTAIN",
            "stage_scores": {},
            "fusion_method": self.fusion_method,
            "stage_contributions": {},
        }


class DualBranchFusion(FusionEngine):
    """
    Dual-branch fusion with separate acoustic and neural branches.
    """

    def __init__(self, **kwargs):
        """Initialize dual-branch fusion."""
        super().__init__(**kwargs)
        self.acoustic_stages = ["feature_extraction", "temporal_analysis", "artifact_detection"]
        self.neural_stages = ["rawnet3"]

    def fuse(self, stage_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fuse results using dual-branch approach.

        Branch 1: Acoustic features (stages 1-3)
        Branch 2: Neural network (stage 4)
        """
        # Get base fusion result
        result = super().fuse(stage_results)

        if not result.get("success", False):
            return result

        # Compute branch-specific scores
        scores = self._extract_scores(stage_results)

        acoustic_scores = {k: v for k, v in scores.items() if k in self.acoustic_stages}
        neural_scores = {k: v for k, v in scores.items() if k in self.neural_stages}

        acoustic_score = self._weighted_average_fusion(acoustic_scores) if acoustic_scores else 0.5
        neural_score = self._weighted_average_fusion(neural_scores) if neural_scores else 0.5

        # Add branch information
        result["branch_scores"] = {
            "acoustic": float(acoustic_score),
            "neural": float(neural_score),
        }

        # Check for branch disagreement
        result["branch_agreement"] = abs(acoustic_score - neural_score) < 0.3

        return result
