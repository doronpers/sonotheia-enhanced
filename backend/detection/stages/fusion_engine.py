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
        stage_weights: Optional[Dict[str, float]] = None,
        confidence_threshold: float = 0.5,
        decision_threshold: float = 0.5,
        **kwargs
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
        self.profiles = kwargs.get("profiles", {}) # Store fusion profiles
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
            
            # --- DUAL-FACTOR VERIFICATION (PROSECUTOR vs DEFENSE) ---
            # Architecture:
            # 1. Prosecution (Risk): Violation of Physics -> High Confidence FAKE
            # 2. Defense (Trust): Presence of Life Signs -> Confidence Boost for REAL
            
            physics = stage_results.get("physics_analysis", {})
            sensor_results = physics.get("sensor_results", {}) if physics.get("success") else {}
            
            risk_scores = []
            trust_scores = []
            
            for name, res in sensor_results.items():
                # Extract score/value
                val = res.get("value", 0.0)
                # Determine category (default to defense if not found, but we tagged them)
                # Note: We need access to the sensor instance or metadata to know category.
                # Since we don't have the instance here, we rely on mapped names or metadata.
                # Ideally, metadata['category'] should be passed in result.
                # WORKAROUND: Map known names until pipeline passes category in result.metadata
                category = "defense"
                lower_name = name.lower()
                if "glottal" in lower_name or "pitch velocity" in lower_name or "silence" in lower_name or "two-mouth" in lower_name:
                    category = "prosecution"
                
                # Check optional metadata override
                if res.get("metadata", {}).get("category"):
                     category = res.get("metadata", {}).get("category")

                if category == "prosecution":
                    risk_scores.append(val)
                else:
                    trust_scores.append(val)

            # 1. Calculate Risk (Max of Prosecution)
            # If any prosecutor finds a violation, Risk is high.
            risk_score = max(risk_scores) if risk_scores else 0.0
            
            # 2. Calculate Trust (Avg of Defense)
            # consistently good defense signs build trust.
            trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0.5
            
            # 3. The Verdict Matrix
            # Default to weighted average of all stages
            base_score = self._weighted_average_fusion(scores)
            
            final_score = base_score
            decision_logic = "Weighted Average"
            
            # Logic: High Risk trumps everything (Veto)
            if risk_score > 0.8:
                final_score = max(final_score, risk_score)
                decision_logic = "Prosecution Veto (High Risk)"
            
            # Logic: Low Risk + High Trust = Boost Real
            elif risk_score < 0.3 and trust_score < 0.3: # Trust sensors return low score for Real (0.0=Real)
                 # If Trust is high (meaning scores are low/passed), we pull the score down
                 final_score = min(final_score, 0.2)
                 decision_logic = "Defense Validation (High Trust)"

            # ---------------------------------------

            if not scores:
                return self._empty_result("No valid scores to fuse")

            # Compute overall confidence
            confidence = self._compute_confidence(stage_results, scores)

            # Make decision
            is_spoof = final_score > self.decision_threshold
            decision = self._make_decision(final_score, confidence)

            # Apply Rule-Based Arbiter (Veto/Override Logic)
            # (Kept as safety net, though Prosecution logic covers most)
            arbiter_result = self._apply_arbiter_rules(stage_results, final_score, decision)
            
            # Use Arbiter's overrides if any
            final_score = arbiter_result.get("fused_score", final_score)
            final_decision = arbiter_result.get("decision", decision)
            arbiter_explanation = arbiter_result.get("explanation", "")

            return {
                "success": True,
                "fused_score": float(final_score),
                "risk_score": float(risk_scores[0] if risk_scores else 0.0), # Example for UI
                "trust_score": float(trust_scores[0] if trust_scores else 0.0), # Example for UI
                "confidence": float(confidence),
                "is_spoof": final_score > self.decision_threshold,
                "decision": final_decision,
                "stage_scores": scores,
                "fusion_method": decision_logic, # Return logic used
                "stage_contributions": self._compute_contributions(scores, final_score),
                "arbiter_override": arbiter_result.get("override_applied", False),
                "arbiter_details": arbiter_explanation
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
        Currently falls back to weighted average fusion as learned models
        are not yet implemented.

        Note: This is a placeholder - actual learned fusion would require
        training a fusion model on labeled data.
        """
        # For now, fall back to weighted average
        logger.warning("Learned fusion not implemented, falling back to weighted average")
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



    def _apply_arbiter_rules(
        self, 
        stage_results: Dict[str, Dict[str, Any]], 
        current_score: float, 
        current_decision: str
    ) -> Dict[str, Any]:
        """
        Apply rule-based arbitration to override statistical fusion.
        
        Implements constraints from physics sensors that should act as "Vetoes"
        rather than just weighted inputs.
        
        Rules:
        1. Two-Mouth Violation: Word overlapping (impossible for single speaker) -> High Fake Probability
        2. Breath Pattern Violation: Impossible lung capacity or double-breaths -> High Fake Probability
        3. Glottal Inertia: If 100% clean (no violations), boost Trust (lower Fake Score)
        """
        physics = stage_results.get("physics_analysis", {})
        if not physics.get("success", False):
            return {"override_applied": False, "fused_score": current_score, "decision": current_decision}

        sensor_results = physics.get("sensor_results", {})
        overrides = []
        new_score = current_score
        
        # Rule 1: Two-Mouth (Word Overlap)
        # DISABLED (Checking 2025-12-09: Sensor accuracy ~50%, causing false alarms)
        # two_mouth = sensor_results.get("TwoMouthSensor", {})
        # if two_mouth.get("value", 0.0) > 0.5: # Threshold for high confidence artifact
        #     overrides.append("Two-Mouth Artifact Detected (Word Overlap)")
        #     new_score = max(new_score, 0.95) # Near certainty

            
        # Rule 2: Breath Patterns (Infinite Lung Capacity / Double Breath)
        # Respiration violation implies impossible breathing
        breath = sensor_results.get("Breath Sensor (Max Phonation)", {}) # Name check needed
        breath_meta = breath.get("metadata", {})
        if breath_meta.get("respiration_violation", False):
            overrides.append("Impossible Breath Pattern (Infinite Lung Capacity)")
            new_score = max(new_score, 0.90)
            
        # Rule 3: Glottal Inertia (Trust Booster)
        glottal = sensor_results.get("Glottal Inertia Sensor", {})
        glottal_meta = glottal.get("metadata", {})
        violation_count = glottal_meta.get("violation_count", 0)
        
        if violation_count > 0:
             # If physics violated, ensure score is at least high
             overrides.append(f"Glottal Physics Violation ({violation_count} events)")
             new_score = max(new_score, 0.85) 
        elif glottal.get("passed") is True and violation_count == 0:
             # Trust Boost: Validated human physics
             # Only reduce score if we don't have other fatal strikes (TwoMouth/Breath)
             if len(overrides) == 0: 
                 trust_factor = 0.5
                 previous_score = new_score
                 new_score = new_score * trust_factor
                 if previous_score > 0.5 and new_score < 0.5:
                      overrides.append("Glottal Physics Validation (Trust Boost)")

        if not overrides:
            return {"override_applied": False, "fused_score": current_score, "decision": current_decision}
            
        # Determine new decision based on overridden score
        new_decision = self._make_decision(new_score, 1.0) # High confidence in rules
        
        return {
            "override_applied": True,
            "fused_score": new_score, 
            "decision": new_decision,
            "explanation": "; ".join(overrides)
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
