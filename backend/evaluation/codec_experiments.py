"""
Codec Experiments and Evaluation

Run experiments to test spoof detection under different codec conditions.
"""

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve
from typing import List, Dict, Callable, Tuple
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def compute_eer(genuine_scores: np.ndarray, spoof_scores: np.ndarray) -> Tuple[float, float]:
    """
    Compute Equal Error Rate (EER)

    Args:
        genuine_scores: Scores for genuine samples
        spoof_scores: Scores for spoof samples

    Returns:
        Tuple of (EER, threshold at EER)
    """
    # Create labels (0 = genuine, 1 = spoof)
    y_true = np.concatenate([
        np.zeros(len(genuine_scores)),
        np.ones(len(spoof_scores))
    ])

    y_scores = np.concatenate([genuine_scores, spoof_scores])

    # Compute ROC curve
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)

    # Find EER point where FAR = FRR (i.e., FPR = 1 - TPR)
    fnr = 1 - tpr
    eer_idx = np.nanargmin(np.abs(fpr - fnr))
    eer = (fpr[eer_idx] + fnr[eer_idx]) / 2
    eer_threshold = thresholds[eer_idx] if eer_idx < len(thresholds) else 0.5

    return float(eer), float(eer_threshold)


def compute_metrics(genuine_scores: np.ndarray, spoof_scores: np.ndarray) -> Dict[str, float]:
    """
    Compute detection metrics

    Args:
        genuine_scores: Scores for genuine samples
        spoof_scores: Scores for spoof samples

    Returns:
        Dictionary of metrics
    """
    # Create labels
    y_true = np.concatenate([
        np.zeros(len(genuine_scores)),
        np.ones(len(spoof_scores))
    ])

    y_scores = np.concatenate([genuine_scores, spoof_scores])

    # Compute metrics
    eer, eer_threshold = compute_eer(genuine_scores, spoof_scores)
    auc = roc_auc_score(y_true, y_scores)

    # Additional statistics
    metrics = {
        'eer': eer,
        'eer_threshold': eer_threshold,
        'auc': auc,
        'mean_genuine_score': float(np.mean(genuine_scores)),
        'mean_spoof_score': float(np.mean(spoof_scores)),
        'std_genuine_score': float(np.std(genuine_scores)),
        'std_spoof_score': float(np.std(spoof_scores)),
        'num_genuine': len(genuine_scores),
        'num_spoof': len(spoof_scores)
    }

    return metrics


def run_codec_experiment(
    audio_paths: List[str],
    labels: List[int],
    codec_chain_fn: Callable,
    feature_extractor_fn: Callable,
    model_predict_fn: Callable,
    codec_name: str = "unknown"
) -> Dict[str, any]:
    """
    Run codec experiment

    Args:
        audio_paths: List of audio file paths
        labels: List of labels (0=genuine, 1=spoof)
        codec_chain_fn: Function to apply codec effects
        feature_extractor_fn: Function to extract features
        model_predict_fn: Function to predict spoof score
        codec_name: Name of codec for reporting

    Returns:
        Dictionary with experiment results
    """
    logger.info(f"Running codec experiment: {codec_name}")

    genuine_scores = []
    spoof_scores = []

    from data_ingest.loader import AudioLoader
    loader = AudioLoader()

    for audio_path, label in zip(audio_paths, labels):
        try:
            # Load audio
            audio, sr = loader.load_wav(audio_path)

            # Apply codec
            audio_coded = codec_chain_fn(audio, sr)

            # Extract features
            features = feature_extractor_fn(audio_coded, sr)

            # Predict score
            score = model_predict_fn(features)

            # Store score
            if label == 0:
                genuine_scores.append(score)
            else:
                spoof_scores.append(score)

        except Exception as e:
            logger.error(f"Error processing {audio_path}: {str(e)}")
            continue

    # Convert to arrays
    genuine_scores = np.array(genuine_scores)
    spoof_scores = np.array(spoof_scores)

    # Compute metrics
    metrics = compute_metrics(genuine_scores, spoof_scores)
    metrics['codec'] = codec_name

    logger.info(f"Codec: {codec_name}, EER: {metrics['eer']:.4f}, AUC: {metrics['auc']:.4f}")

    return metrics


def run_multi_codec_experiment(
    audio_paths: List[str],
    labels: List[int],
    codec_chains: Dict[str, Callable],
    feature_extractor_fn: Callable,
    model_predict_fn: Callable,
    output_path: str = None
) -> List[Dict[str, any]]:
    """
    Run experiments across multiple codec conditions

    Args:
        audio_paths: List of audio file paths
        labels: List of labels
        codec_chains: Dictionary mapping codec names to codec functions
        feature_extractor_fn: Feature extraction function
        model_predict_fn: Model prediction function
        output_path: Optional path to save results JSON

    Returns:
        List of result dictionaries
    """
    results = []

    for codec_name, codec_fn in codec_chains.items():
        metrics = run_codec_experiment(
            audio_paths=audio_paths,
            labels=labels,
            codec_chain_fn=codec_fn,
            feature_extractor_fn=feature_extractor_fn,
            model_predict_fn=model_predict_fn,
            codec_name=codec_name
        )
        results.append(metrics)

    # Save results if output path provided
    if output_path:
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'num_files': len(audio_paths),
            'results': results
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Results saved to {output_path}")

    return results


def print_results_table(results: List[Dict[str, any]]):
    """
    Print results in a formatted table

    Args:
        results: List of result dictionaries
    """
    print("\n" + "="*70)
    print("Codec Experiment Results")
    print("="*70)
    print(f"{'Codec':<15} {'EER':<10} {'AUC':<10} {'Genuine':<15} {'Spoof':<15}")
    print("-"*70)

    for result in results:
        codec = result['codec']
        eer = result['eer']
        auc = result['auc']
        mean_gen = result['mean_genuine_score']
        mean_spoof = result['mean_spoof_score']

        print(f"{codec:<15} {eer:<10.4f} {auc:<10.4f} {mean_gen:<15.4f} {mean_spoof:<15.4f}")

    print("="*70 + "\n")
