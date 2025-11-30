#!/usr/bin/env python
"""
Evaluate Fusion Engine

Evaluates the dual-branch fusion engine on test datasets.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from detection import DetectionPipeline, DetectionConfig
from detection.stages import FusionEngine, DualBranchFusion
from detection.utils import convert_numpy_types
from evaluation.metrics import compute_all_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_fusion_methods(
    genuine_scores: list[dict],
    spoof_scores: list[dict],
    output_dir: str = None,
) -> dict:
    genuine_scores: dict,
    spoof_scores: dict,
    output_dir: str = None,
) -> dict:
    """
    Evaluate different fusion methods.

    Args:
        genuine_scores: Stage scores for genuine samples
        spoof_scores: Stage scores for spoof samples
        output_dir: Directory to save results

    Returns:
        Evaluation results
    """
    results = {}

    # Test different fusion methods
    fusion_methods = ["weighted_average", "max"]

    for method in fusion_methods:
        logger.info(f"Evaluating fusion method: {method}")

        fusion = FusionEngine(fusion_method=method)

        genuine_fused = []
        for scores in genuine_scores:
            result = fusion.fuse(scores)
            genuine_fused.append(result.get("fused_score", 0.5))

        spoof_fused = []
        for scores in spoof_scores:
            result = fusion.fuse(scores)
            spoof_fused.append(result.get("fused_score", 0.5))

        # Compute metrics
        y_true = np.array([0] * len(genuine_fused) + [1] * len(spoof_fused))
        y_scores = np.array(genuine_fused + spoof_fused)

        metrics = compute_all_metrics(y_true, y_scores, threshold=0.5)
        results[method] = metrics

        logger.info(f"  AUC: {metrics['auc']:.4f}, Accuracy: {metrics['accuracy']:.4f}")

    # Test dual-branch fusion
    logger.info("Evaluating dual-branch fusion")
    dual_fusion = DualBranchFusion()

    genuine_fused = []
    for scores in genuine_scores:
        result = dual_fusion.fuse(scores)
        genuine_fused.append(result.get("fused_score", 0.5))

    spoof_fused = []
    for scores in spoof_scores:
        result = dual_fusion.fuse(scores)
        spoof_fused.append(result.get("fused_score", 0.5))

    y_true = np.array([0] * len(genuine_fused) + [1] * len(spoof_fused))
    y_scores = np.array(genuine_fused + spoof_fused)

    metrics = compute_all_metrics(y_true, y_scores, threshold=0.5)
    results["dual_branch"] = metrics

    logger.info(f"  AUC: {metrics['auc']:.4f}, Accuracy: {metrics['accuracy']:.4f}")

    # Save results
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results_file = output_path / f"fusion_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(convert_numpy_types(results), f, indent=2)
        logger.info(f"Results saved to {results_file}")

    return results


def generate_synthetic_scores(n_samples: int = 100) -> tuple:
    """Generate synthetic stage scores for testing."""
    np.random.seed(42)

    # Generate genuine scores (lower values)
    genuine = []
    for _ in range(n_samples):
        scores = {
            "feature_extraction": {
                "success": True,
                "anomaly_score": np.random.beta(2, 5),
            },
            "temporal_analysis": {
                "success": True,
                "temporal_score": np.random.beta(2, 5),
            },
            "artifact_detection": {
                "success": True,
                "artifact_score": np.random.beta(2, 5),
            },
            "rawnet3": {
                "success": True,
                "score": np.random.beta(2, 5),
            },
        }
        genuine.append(scores)

    # Generate spoof scores (higher values)
    spoof = []
    for _ in range(n_samples):
        scores = {
            "feature_extraction": {
                "success": True,
                "anomaly_score": np.random.beta(5, 2),
            },
            "temporal_analysis": {
                "success": True,
                "temporal_score": np.random.beta(5, 2),
            },
            "artifact_detection": {
                "success": True,
                "artifact_score": np.random.beta(5, 2),
            },
            "rawnet3": {
                "success": True,
                "score": np.random.beta(5, 2),
            },
        }
        spoof.append(scores)

    return genuine, spoof


def main():
    parser = argparse.ArgumentParser(description="Evaluate Fusion Engine")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation_results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=100,
        help="Number of synthetic samples per class",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        default=True,
        help="Use synthetic data (default)",
    )

    args = parser.parse_args()

    logger.info("Starting fusion engine evaluation")

    # Generate synthetic data
    genuine_scores, spoof_scores = generate_synthetic_scores(args.n_samples)

    # Evaluate
    results = evaluate_fusion_methods(
        genuine_scores,
        spoof_scores,
        output_dir=args.output_dir,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("FUSION ENGINE EVALUATION SUMMARY")
    print("=" * 60)

    for method, metrics in results.items():
        print(f"\n{method.upper()}:")
        print(f"  AUC:       {metrics['auc']:.4f}")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1_score']:.4f}")

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
