"""
Stage 6: Explainability

Generates explanations for detection results.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional

import numpy as np
from huggingface_hub import InferenceClient

from backend.utils.serialization import convert_numpy_types

logger = logging.getLogger(__name__)


class ExplainabilityStage:
    """
    Stage 6: Explainability

    Generates human-readable explanations for detection results:
    - Feature importance analysis
    - Temporal segment explanations
    - Artifact descriptions
    - Overall decision reasoning
    """

    def __init__(
        self,
        generate_saliency: bool = True,
        include_feature_importance: bool = True,
        include_temporal_segments: bool = True,
        max_top_features: int = 10,
        detail_level: str = "standard",
        llm_model_id: str = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        enable_llm: bool = True,
    ):
        """
        Initialize explainability stage.

        Args:
            generate_saliency: Whether to generate saliency maps
            include_feature_importance: Include feature importance
            include_temporal_segments: Include temporal segment analysis
            max_top_features: Maximum number of top features to report
            detail_level: Explanation detail ("minimal", "standard", "detailed")
            llm_model_id: Hugging Face model ID for LLM analysis
            enable_llm: Whether to enable LLM-based analysis
        """
        self.generate_saliency = generate_saliency
        self.include_feature_importance = include_feature_importance
        self.include_temporal_segments = include_temporal_segments
        self.max_top_features = max_top_features
        self.detail_level = detail_level
        self.llm_model_id = llm_model_id
        self.enable_llm = enable_llm

        self.client = None
        if self.enable_llm:
            token = os.getenv("HUGGINGFACE_TOKEN")
            if token:
                try:
                    self.client = InferenceClient(model=llm_model_id, token=token)
                    logger.info(f"LLM enabled: {llm_model_id}")
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM client: {e}")
            else:
                logger.warning("HUGGINGFACE_TOKEN not found. LLM explainability disabled.")

        logger.info(f"ExplainabilityStage initialized: detail_level={detail_level}")

    def process(
        self,
        stage_results: Dict[str, Dict[str, Any]],
        fusion_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate explanations for detection results.

        Args:
            stage_results: Results from all detection stages
            fusion_result: Fused detection result

        Returns:
            Dictionary containing explanations
        """
        try:
            # Generate overall summary
            summary = self._generate_summary(fusion_result)

            # Generate stage-specific explanations
            stage_explanations = self._explain_stages(stage_results)

            # Generate feature importance (if applicable)
            feature_importance = {}
            if self.include_feature_importance and "feature_extraction" in stage_results:
                feature_importance = self._analyze_feature_importance(
                    stage_results["feature_extraction"]
                )

            # Generate temporal explanations (if applicable)
            temporal_explanations = {}
            if self.include_temporal_segments and "temporal_analysis" in stage_results:
                temporal_explanations = self._explain_temporal(
                    stage_results["temporal_analysis"]
                )

            # Generate artifact explanations
            artifact_explanations = {}
            if "artifact_detection" in stage_results:
                artifact_explanations = self._explain_artifacts(
                    stage_results["artifact_detection"]
                )

            # Generate reasoning chain
            reasoning = self._generate_reasoning_chain(
                stage_results, fusion_result, summary
            )

            # LLM Enhancement (Forensic Analysis)
            if self.client:
                llm_insight = self._query_llm(stage_results, fusion_result)
                if llm_insight:
                    # Override summary with expert analysis if available
                    if "summary" in llm_insight and llm_insight["summary"]:
                        summary = llm_insight["summary"]
                    # Append expert reasoning
                    if "reasoning_chain" in llm_insight and llm_insight["reasoning_chain"]:
                        reasoning.extend(llm_insight["reasoning_chain"])

            # Compute explainability score
            explainability_score = self._compute_explainability_score(
                stage_results, fusion_result
            )

            return {
                "success": True,
                "summary": summary,
                "stage_explanations": stage_explanations,
                "feature_importance": feature_importance,
                "temporal_explanations": temporal_explanations,
                "artifact_explanations": artifact_explanations,
                "reasoning_chain": reasoning,
                "explainability_score": float(explainability_score),
                "confidence_factors": self._get_confidence_factors(
                    stage_results, fusion_result
                ),
            }

        except Exception as e:
            logger.error(f"Explainability processing failed: {e}")
            return self._empty_result(str(e))

    def _generate_summary(self, fusion_result: Dict[str, Any]) -> str:
        """Generate high-level summary of detection result."""
        score = fusion_result.get("fused_score", 0.5)
        decision = fusion_result.get("decision", "UNCERTAIN")
        confidence = fusion_result.get("confidence", 0.0)

        if decision == "SPOOF_HIGH":
            summary = (
                f"HIGH CONFIDENCE SPOOF DETECTED. "
                f"The audio shows strong indicators of synthetic generation or manipulation. "
                f"Detection score: {score:.2f}, Confidence: {confidence:.2f}."
            )
        elif decision == "SPOOF_LIKELY":
            summary = (
                f"LIKELY SPOOF. "
                f"The audio exhibits characteristics consistent with deepfake or synthetic audio. "
                f"Detection score: {score:.2f}, Confidence: {confidence:.2f}."
            )
        elif decision == "UNCERTAIN":
            summary = (
                f"UNCERTAIN RESULT. "
                f"The detection result is inconclusive. Manual review recommended. "
                f"Detection score: {score:.2f}, Confidence: {confidence:.2f}."
            )
        else:
            summary = (
                f"LIKELY GENUINE. "
                f"The audio appears to be genuine with no significant indicators of manipulation. "
                f"Detection score: {score:.2f}, Confidence: {confidence:.2f}."
            )

        return summary

    def _explain_stages(self, stage_results: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Generate explanations for each stage."""
        explanations = {}

        for stage_name, result in stage_results.items():
            if not result.get("success", False):
                explanations[stage_name] = "Stage failed to produce results."
                continue

            explanation = self._explain_single_stage(stage_name, result)
            explanations[stage_name] = explanation

        return explanations

    def _explain_single_stage(self, stage_name: str, result: Dict[str, Any]) -> str:
        """Generate explanation for a single stage."""
        if stage_name == "feature_extraction":
            score = result.get("anomaly_score", 0.5)
            num_frames = result.get("num_frames", 0)
            return (
                f"Feature analysis extracted {num_frames} frames with anomaly score {score:.3f}. "
                f"{'Elevated anomaly score suggests unusual acoustic patterns.' if score > 0.5 else 'Feature patterns appear normal.'}"
            )

        elif stage_name == "temporal_analysis":
            score = result.get("temporal_score", 0.5)
            num_anomalies = result.get("num_anomalies", 0)
            return (
                f"Temporal analysis found {num_anomalies} potential anomalies with score {score:.3f}. "
                f"{'Discontinuities or unusual transitions detected.' if num_anomalies > 5 else 'Temporal flow appears natural.'}"
            )

        elif stage_name == "artifact_detection":
            score = result.get("artifact_score", 0.5)
            total = result.get("total_artifacts", 0)
            return (
                f"Artifact detection found {total} artifacts with score {score:.3f}. "
                f"{'Significant audio artifacts present.' if total > 10 else 'Minimal artifacts detected.'}"
            )

        elif stage_name == "rawnet3":
            score = result.get("score", 0.5)
            demo = result.get("demo_mode", True)
            return (
                f"Neural network analysis produced score {score:.3f}. "
                f"{'(DEMO MODE - not production score) ' if demo else ''}"
                f"{'Model indicates synthetic characteristics.' if score > 0.5 else 'Model indicates genuine characteristics.'}"
            )

        else:
            return f"Stage {stage_name} completed."

    def _analyze_feature_importance(self, fe_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feature importance from feature extraction results."""
        importance = {}
        feature_stats = fe_result.get("feature_stats", {})

        for feat_type, stats in feature_stats.items():
            # Use variance as proxy for importance
            std = stats.get("std", 0.0)
            importance[feat_type] = {
                "importance_score": min(std / 5.0, 1.0),
                "mean": stats.get("mean", 0.0),
                "std": std,
            }

        # Sort by importance
        sorted_features = sorted(
            importance.items(), key=lambda x: x[1]["importance_score"], reverse=True
        )

        return {
            "top_features": dict(sorted_features[: self.max_top_features]),
            "total_features_analyzed": len(importance),
        }

    def _explain_temporal(self, ta_result: Dict[str, Any]) -> Dict[str, Any]:
        """Explain temporal analysis results."""
        segments = ta_result.get("suspicious_segments", [])
        discontinuities = ta_result.get("discontinuities", {})

        explanations = []
        for seg in segments[:5]:  # Limit to top 5
            exp = (
                f"Suspicious segment at {seg.get('start_time', 0):.2f}s - {seg.get('end_time', 0):.2f}s "
                f"(confidence: {seg.get('confidence', 0):.2f}, type: {seg.get('type', 'unknown')})"
            )
            explanations.append(exp)

        return {
            "segment_explanations": explanations,
            "num_discontinuities": len(discontinuities.get("positions", [])),
            "temporal_summary": (
                f"Found {len(segments)} suspicious segments and "
                f"{len(discontinuities.get('positions', []))} discontinuities."
            ),
        }

    def _explain_artifacts(self, ad_result: Dict[str, Any]) -> Dict[str, Any]:
        """Explain artifact detection results."""
        artifacts = ad_result.get("all_artifacts", [])

        # Group by type
        by_type = {}
        for artifact in artifacts:
            art_type = artifact.get("type", "unknown")
            if art_type not in by_type:
                by_type[art_type] = []
            by_type[art_type].append(artifact)

        explanations = []
        for art_type, items in by_type.items():
            explanations.append(f"{len(items)} {art_type} artifact(s) detected")

        return {
            "by_type": {k: len(v) for k, v in by_type.items()},
            "explanations": explanations,
            "total_artifacts": len(artifacts),
        }

    def _generate_reasoning_chain(
        self,
        stage_results: Dict[str, Dict[str, Any]],
        fusion_result: Dict[str, Any],
        summary: str,
    ) -> List[str]:
        """Generate step-by-step reasoning chain."""
        reasoning = []

        # Step 1: Feature analysis
        if "feature_extraction" in stage_results:
            fe = stage_results["feature_extraction"]
            reasoning.append(
                f"1. Feature extraction analyzed {fe.get('num_frames', 0)} frames "
                f"with anomaly score {fe.get('anomaly_score', 0.5):.3f}."
            )

        # Step 2: Temporal analysis
        if "temporal_analysis" in stage_results:
            ta = stage_results["temporal_analysis"]
            reasoning.append(
                f"2. Temporal analysis found {ta.get('num_anomalies', 0)} anomalies "
                f"with score {ta.get('temporal_score', 0.5):.3f}."
            )

        # Step 3: Artifact detection
        if "artifact_detection" in stage_results:
            ad = stage_results["artifact_detection"]
            reasoning.append(
                f"3. Artifact detection found {ad.get('total_artifacts', 0)} artifacts "
                f"with score {ad.get('artifact_score', 0.5):.3f}."
            )

        # Step 4: Neural network
        if "rawnet3" in stage_results:
            rn = stage_results["rawnet3"]
            reasoning.append(
                f"4. RawNet3 neural network produced score {rn.get('score', 0.5):.3f}"
                f"{' (DEMO MODE)' if rn.get('demo_mode', True) else ''}."
            )

        # Step 5: Fusion
        reasoning.append(
            f"5. Scores fused using {fusion_result.get('fusion_method', 'unknown')} "
            f"to produce final score {fusion_result.get('fused_score', 0.5):.3f}."
        )

        # Step 6: Decision
        reasoning.append(f"6. Final decision: {fusion_result.get('decision', 'UNCERTAIN')}.")

        return reasoning

    def _compute_explainability_score(
        self,
        stage_results: Dict[str, Dict[str, Any]],
        fusion_result: Dict[str, Any],
    ) -> float:
        """Compute how well the result can be explained."""
        factors = []

        # Check if all stages succeeded
        success_rate = sum(
            1 for r in stage_results.values() if r.get("success", False)
        ) / max(len(stage_results), 1)
        factors.append(success_rate)

        # Check confidence level
        confidence = fusion_result.get("confidence", 0.0)
        factors.append(confidence)

        # Check if score is decisive (not near 0.5)
        score = fusion_result.get("fused_score", 0.5)
        decisiveness = abs(score - 0.5) * 2
        factors.append(decisiveness)

        return float(np.mean(factors))

    def _get_confidence_factors(
        self,
        stage_results: Dict[str, Dict[str, Any]],
        fusion_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Get factors affecting confidence."""
        factors = []

        # Demo mode warning
        for stage_name, result in stage_results.items():
            if result.get("demo_mode", False):
                factors.append({
                    "factor": "demo_mode",
                    "impact": "negative",
                    "description": f"{stage_name} is running in DEMO MODE - scores are placeholder values.",
                })

        # Check for failed stages
        for stage_name, result in stage_results.items():
            if not result.get("success", False):
                factors.append({
                    "factor": "stage_failure",
                    "impact": "negative",
                    "description": f"{stage_name} failed: {result.get('error', 'unknown error')}",
                })

        # Check for model fallback behavior (e.g., missing weights)
        for stage_name, result in stage_results.items():
            model_output = result.get("model_output", {})
            if isinstance(model_output, dict):
                if "message" in model_output and "placeholder" in model_output.get("message", "").lower():
                    factors.append({
                        "factor": "model_fallback",
                        "impact": "negative",
                        "description": f"{stage_name} using fallback/placeholder behavior.",
                    })

        # Check branch agreement
        if "branch_agreement" in fusion_result:
            if not fusion_result["branch_agreement"]:
                factors.append({
                    "factor": "branch_disagreement",
                    "impact": "negative",
                    "description": "Acoustic and neural branches disagree significantly.",
                })

        # Check for low confidence scores
        if fusion_result.get("confidence", 1.0) < 0.5:
            factors.append({
                "factor": "low_confidence",
                "impact": "negative",
                "description": "Overall detection confidence is below 50%.",
            })

        return factors

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed explainability."""
        return {
            "success": False,
            "error": error_msg,
            "summary": "Explanation generation failed.",
            "stage_explanations": {},
            "feature_importance": {},
            "temporal_explanations": {},
            "artifact_explanations": {},
            "reasoning_chain": [],
            "explainability_score": 0.0,
            "confidence_factors": [],
        }

    def _query_llm(
        self,
        stage_results: Dict[str, Dict[str, Any]],
        fusion_result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Query LLM for forensic analysis using chat completion (Mistral compatible).
        """
        try:
            # Construct context
            context = {
                "fusion": {
                    "score": fusion_result.get("fused_score"),
                    "verdict": fusion_result.get("decision"),
                    "confidence": fusion_result.get("confidence")
                },
                "sensors": {}
            }
            
            # Physics
            if "physics_analysis" in stage_results:
                phys = stage_results["physics_analysis"].get("sensor_results", {})
                for k, v in phys.items():
                    context["sensors"][k] = {
                        "score": v.get("score"), 
                        "passed": v.get("passed", False),
                        "details": v.get("metadata", {})
                    }

            # RawNet
            if "rawnet3" in stage_results:
                rn = stage_results["rawnet3"]
                context["sensors"]["RawNet3"] = {
                    "score": rn.get("score"),
                    "is_demo": rn.get("demo_mode", False)
                }

            # Ensure context is JSON serializable (convert numpy float32 to float)
            context = convert_numpy_types(context)

            # Use chat completion for robust template handling
            messages = [
                {
                    "role": "system",
                    "content": "You are a Forensic Audio Analyst for Sonotheia. Analyze the provided JSON detection data and provide a concise, expert conclusion."
                },
                {
                    "role": "user",
                    "content": f"""Context:
- High scores (>0.5) indicate FAKE/SYNTHETIC access.
- Low scores (<0.5) indicate REAL/ORGANIC access.
- "Breath Sensor" detects breathing. Absence is suspicious.
- "Phase Coherence" detects vocoder artifacts (0.0 is perfect machine phase, suspicious).
- "RawNet3" is a deep learning detector.

Data:
{json.dumps(context, indent=2)}

Provide your analysis in this JSON format (no markdown):
{{
  "summary": "A 1-2 sentence expert conclusion.",
  "reasoning_chain": ["Observation 1...", "Observation 2...", "Conclusion..."]
}}"""
                }
            ]

            response = self.client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json"}  # Enforce JSON if supported
            )
            
            # Extract content from chat completion message
            # Safety: Check if choices exist and have at least one item
            if not hasattr(response, 'choices') or not response.choices:
                raise ValueError("LLM response has no choices")
            if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
                raise ValueError("LLM response choice missing message or content")
            content = response.choices[0].message.content
            
            # Simple cleanup to ensure valid JSON
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "").replace("```", "")
            elif cleaned.startswith("```"):
                cleaned = cleaned.replace("```", "")
            
            return json.loads(cleaned)

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if e else "Unknown error"
            # Log full exception details for debugging
            logger.warning(
                f"LLM Query failed: {error_type}: {error_msg}",
                exc_info=True  # Include full traceback for debugging
            )
            return None

