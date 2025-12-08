"""
Liveness / Spoof Evaluation Harness

Purpose: Offline accuracy-first evaluation of the current spoof/liveness
detector for suspicious-call scenarios where speed can be traded for accuracy.

Inputs:
- Dataset metadata CSV with columns: file_path, label (0=genuine, 1=spoof)
- Audio files located relative to dataset_dir
- Optional trained GMM model path (defaults to placeholder if missing)

Outputs:
- JSON metrics (AUC, EER, threshold at target FPR, TPR at target FPR)
- CSV of per-file scores
- ROC and DET plots (saved to output directory)

Usage:
    python backend/scripts/eval_liveness.py \\
        --dataset-dir backend/data/test_dataset \\
        --metadata-file metadata.csv \\
        --model-path backend/models/gmm_test.pkl \\
        --output-dir backend/eval_results
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

# Local imports
from data_ingest.loader import AudioLoader
from telephony.pipeline import TelephonyPipeline
from features.extraction import FeatureExtractor
from models.baseline import GMMSpoofDetector
from evaluation.metrics import plot_roc_curve, plot_det_curve, plot_score_distributions

logger = logging.getLogger("eval_liveness")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def load_dataset(metadata_path: Path, dataset_dir: Path) -> Tuple[List[str], np.ndarray]:
    """Load audio paths and labels from metadata CSV."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    df = pd.read_csv(metadata_path)
    required_cols = {"file_path", "label"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Metadata CSV missing columns: {', '.join(sorted(missing_cols))}")

    audio_paths = [str(dataset_dir / p) for p in df["file_path"]]
    labels = df["label"].to_numpy(dtype=np.int32)

    logger.info(
        "Loaded dataset: %d files (genuine=%d, spoof=%d)",
        len(audio_paths),
        int(np.sum(labels == 0)),
        int(np.sum(labels == 1)),
    )
    return audio_paths, labels


def load_detector(model_path: Path) -> Tuple[GMMSpoofDetector, bool]:
    """
    Load trained spoof detector if available.
    Returns detector instance and flag indicating whether a model was loaded.
    """
    detector = GMMSpoofDetector()
    model_loaded = False

    if model_path and model_path.exists():
        try:
            detector.load(str(model_path))
            model_loaded = True
            logger.info("Loaded spoof detector from %s", model_path)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to load model at %s: %s", model_path, exc)

    if not model_loaded:
        logger.warning("No trained model loaded. Placeholder heuristic scores will be used.")

    return detector, model_loaded


def compute_eer(fpr: np.ndarray, tpr: np.ndarray) -> Tuple[float, float]:
    """
    Compute Equal Error Rate (where FPR ~= FNR) and the associated threshold index.
    Returns (eer, idx).
    """
    fnr = 1 - tpr
    abs_diffs = np.abs(fpr - fnr)
    idx = np.argmin(abs_diffs)
    eer = max(fpr[idx], fnr[idx])
    return float(eer), int(idx)


def find_threshold_at_fpr(fpr: np.ndarray, thresholds: np.ndarray, target_fpr: float) -> Tuple[float, float]:
    """
    Find threshold achieving closest FPR <= target_fpr. Returns (threshold, fpr_at_threshold).
    """
    viable = np.where(fpr <= target_fpr)[0]
    if len(viable) == 0:
        return float(thresholds[-1]), float(fpr[-1])
    idx = viable[-1]
    return float(thresholds[idx]), float(fpr[idx])


def evaluate(
    audio_paths: List[str],
    labels: np.ndarray,
    detector: GMMSpoofDetector,
    model_loaded: bool,
    codec: str,
    sample_rate: int,
    feature_types: List[str],
) -> Dict[str, np.ndarray]:
    """Run inference across dataset and return scores and labels."""
    loader = AudioLoader(target_sr=sample_rate)
    telephony = TelephonyPipeline()
    extractor = FeatureExtractor(sr=sample_rate)

    scores: List[float] = []

    for audio_path, label in zip(audio_paths, labels):
        try:
            audio, sr = loader.load_wav(audio_path)
            audio_coded = telephony.apply_codec_by_name(audio, sr, codec)
            features = extractor.extract_feature_stack(audio_coded, feature_types=feature_types)

            if model_loaded:
                score = detector.predict_score(features)
            else:
                # Placeholder heuristic mirrors pipeline fallback
                variance = float(np.var(features))
                score = min(1.0, max(0.0, variance / 100.0))

            scores.append(score)
        except Exception as exc:
            logger.error("Failed to process %s: %s", audio_path, exc)
            scores.append(0.5)  # Neutral score when processing fails

    return {
        "scores": np.array(scores, dtype=np.float32),
        "labels": labels,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate liveness/spoof detection accuracy (ROC/DET/EER).")
    parser.add_argument("--dataset-dir", type=str, required=True, help="Directory containing audio dataset.")
    parser.add_argument("--metadata-file", type=str, default="metadata.csv", help="Metadata CSV relative to dataset dir.")
    parser.add_argument("--model-path", type=str, default="backend/models/gmm_test.pkl", help="Path to trained GMM model.")
    parser.add_argument("--output-dir", type=str, default="backend/eval_results", help="Directory to store evaluation outputs.")
    parser.add_argument("--codec", type=str, default="landline", help="Codec to simulate (landline|mobile|voip|clean).")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Target sample rate for loading audio.")
    parser.add_argument(
        "--feature-types",
        nargs="+",
        default=["lfcc", "logspec"],
        help="Feature types to extract (passed to FeatureExtractor).",
    )
    parser.add_argument(
        "--target-fpr",
        type=float,
        default=0.01,
        help="Target false positive rate for threshold selection (e.g., 0.01 for 1%).",
    )

    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    metadata_path = dataset_dir / args.metadata_file
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_paths, labels = load_dataset(metadata_path, dataset_dir)

    detector, model_loaded = load_detector(Path(args.model_path))

    results = evaluate(
        audio_paths=audio_paths,
        labels=labels,
        detector=detector,
        model_loaded=model_loaded,
        codec=args.codec,
        sample_rate=args.sample_rate,
        feature_types=args.feature_types,
    )

    scores = results["scores"]
    labels = results["labels"]

    fpr, tpr, thresholds = roc_curve(labels, scores)
    auc = roc_auc_score(labels, scores)
    eer, eer_idx = compute_eer(fpr, tpr)
    threshold_at_fpr, fpr_at_threshold = find_threshold_at_fpr(fpr, thresholds, target_fpr=args.target_fpr)
    tpr_at_target = float(tpr[np.where(fpr <= args.target_fpr)[0][-1]]) if np.any(fpr <= args.target_fpr) else float(tpr[-1])

    metrics: Dict[str, float] = {
        "auc": float(auc),
        "eer": float(eer),
        "eer_threshold": float(thresholds[eer_idx]),
        "threshold_at_target_fpr": threshold_at_fpr,
        "fpr_at_threshold": fpr_at_threshold,
        "tpr_at_target_fpr": tpr_at_target,
        "target_fpr": float(args.target_fpr),
        "model_loaded": bool(model_loaded),
        "codec": args.codec,
        "sample_rate": int(args.sample_rate),
    }

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Save metrics
    metrics_path = output_dir / f"liveness_metrics_{timestamp}.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved metrics to %s", metrics_path)

    # Save scores CSV
    scores_path = output_dir / f"liveness_scores_{timestamp}.csv"
    pd.DataFrame({"file_path": audio_paths, "label": labels, "score": scores}).to_csv(scores_path, index=False)
    logger.info("Saved per-file scores to %s", scores_path)

    # Plots
    roc_path = output_dir / f"roc_{timestamp}.png"
    det_path = output_dir / f"det_{timestamp}.png"
    dist_path = output_dir / f"score_dist_{timestamp}.png"

    plot_roc_curve(labels, scores, output_path=str(roc_path))
    plot_det_curve(labels, scores, output_path=str(det_path))

    genuine_scores = scores[labels == 0]
    spoof_scores = scores[labels == 1]
    plot_score_distributions(genuine_scores, spoof_scores, output_path=str(dist_path))

    logger.info(
        "Evaluation complete. AUC=%.3f, EER=%.3f, TPR@FPR<=%.3f=%.3f",
        auc,
        eer,
        args.target_fpr,
        tpr_at_target,
    )


if __name__ == "__main__":
    main()

