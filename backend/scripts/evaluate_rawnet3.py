#!/usr/bin/env python
"""
Evaluate RawNet3 Model

Evaluates the RawNet3 neural network on test audio samples.
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

from detection.stages import RawNet3Stage
from detection.config import RawNet3Config
from detection.utils import convert_numpy_types, load_audio
from evaluation.metrics import compute_all_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_rawnet3(
    audio_files: list = None,
    model_path: str = None,
    demo_mode: bool = True,
    output_dir: str = None,
) -> dict:
    """
    Evaluate RawNet3 model.

    Args:
        audio_files: List of (audio_path, label) tuples
        model_path: Path to model weights
        demo_mode: Use demo mode
        output_dir: Output directory

    Returns:
        Evaluation results
    """
    config = RawNet3Config(model_path=model_path)
    stage = RawNet3Stage(config=config, demo_mode=demo_mode)

    results = {
        "model_path": model_path,
        "demo_mode": demo_mode,
        "samples_evaluated": 0,
        "predictions": [],
    }

    if audio_files:
        y_true = []
        y_scores = []

        for audio_path, label in audio_files:
            try:
                audio, sr = load_audio(audio_path)
                result = stage.process(audio)

                y_true.append(label)
                y_scores.append(result.get("score", 0.5))

                results["predictions"].append({
                    "file": str(audio_path),
                    "label": label,
                    "score": result.get("score", 0.5),
                    "is_spoof": result.get("is_spoof", False),
                })

            except Exception as e:
                logger.warning(f"Failed to process {audio_path}: {e}")

        results["samples_evaluated"] = len(y_true)

        if len(y_true) > 0:
            metrics = compute_all_metrics(
                np.array(y_true), np.array(y_scores), threshold=0.5
            )
            results["metrics"] = metrics
    else:
        # Demo mode with synthetic audio
        logger.info("No audio files provided, using synthetic audio")
        results["synthetic_test"] = True

        # Generate test samples
        sr = 16000
        duration = 2.0
        n_samples = 10

        for i in range(n_samples):
            # Generate synthetic audio
            t = np.linspace(0, duration, int(sr * duration))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t * (i + 1)) + 0.1 * np.random.randn(len(t))
            audio = audio.astype(np.float32)

            result = stage.process(audio)

            results["predictions"].append({
                "sample_id": i,
                "score": result.get("score", 0.5),
                "is_spoof": result.get("is_spoof", False),
                "demo_mode": result.get("demo_mode", True),
            })

        results["samples_evaluated"] = n_samples

    # Save results
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results_file = output_path / f"rawnet3_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(convert_numpy_types(results), f, indent=2)
        logger.info(f"Results saved to {results_file}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate RawNet3 Model")
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to model weights",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation_results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        default=False,
        help="Use demo mode (placeholder scores)",
    )
    parser.add_argument(
        "--audio-dir",
        type=str,
        default=None,
        help="Directory containing audio files for evaluation",
    )

    args = parser.parse_args()

    logger.info("Starting RawNet3 evaluation")
    logger.info(f"Demo mode: {args.demo_mode}")

    # Prepare audio files if provided
    audio_files = None
    if args.audio_dir:
        audio_dir = Path(args.audio_dir)
        if audio_dir.exists():
            # Expect subdirectories: genuine/ and spoof/
            audio_files = []
            genuine_dir = audio_dir / "genuine"
            spoof_dir = audio_dir / "spoof"

            if genuine_dir.exists():
                for f in genuine_dir.glob("*.wav"):
                    audio_files.append((f, 0))
            if spoof_dir.exists():
                for f in spoof_dir.glob("*.wav"):
                    audio_files.append((f, 1))

            logger.info(f"Found {len(audio_files)} audio files")

    # Evaluate
    results = evaluate_rawnet3(
        audio_files=audio_files,
        model_path=args.model_path,
        demo_mode=args.demo_mode,
        output_dir=args.output_dir,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("RAWNET3 EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Samples evaluated: {results['samples_evaluated']}")
    print(f"Demo mode: {results['demo_mode']}")

    if "metrics" in results:
        metrics = results["metrics"]
        print("\nMetrics:")
        print(f"  AUC:       {metrics['auc']:.4f}")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1_score']:.4f}")

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
