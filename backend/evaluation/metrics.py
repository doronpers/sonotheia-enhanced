"""
Evaluation Metrics

Common metrics for spoof detection evaluation.
"""

import numpy as np
from sklearn.metrics import (
    roc_auc_score, roc_curve, accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix
)
from typing import Dict
import matplotlib.pyplot as plt


def compute_all_metrics(y_true: np.ndarray, y_scores: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """
    Compute all standard metrics

    Args:
        y_true: True labels (0=genuine, 1=spoof)
        y_scores: Predicted scores
        threshold: Classification threshold

    Returns:
        Dictionary of metrics
    """
    # Binary predictions
    y_pred = (y_scores >= threshold).astype(int)

    # Compute metrics
    metrics = {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'precision': float(precision_score(y_true, y_pred, zero_division=0)),
        'recall': float(recall_score(y_true, y_pred, zero_division=0)),
        'f1_score': float(f1_score(y_true, y_pred, zero_division=0)),
        'auc': float(roc_auc_score(y_true, y_scores)),
        'threshold': float(threshold)
    }

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        metrics.update({
            'true_negative': int(tn),
            'false_positive': int(fp),
            'false_negative': int(fn),
            'true_positive': int(tp),
            'fpr': float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
            'fnr': float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        })

    return metrics


def plot_roc_curve(y_true: np.ndarray, y_scores: np.ndarray, output_path: str = None):
    """
    Plot ROC curve

    Args:
        y_true: True labels
        y_scores: Predicted scores
        output_path: Optional path to save plot
    """
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    auc = roc_auc_score(y_true, y_scores)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"ROC curve saved to {output_path}")
    else:
        plt.show()

    plt.close()


def plot_det_curve(y_true: np.ndarray, y_scores: np.ndarray, output_path: str = None):
    """
    Plot Detection Error Tradeoff (DET) curve

    Args:
        y_true: True labels
        y_scores: Predicted scores
        output_path: Optional path to save plot
    """
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    fnr = 1 - tpr

    plt.figure(figsize=(8, 6))
    plt.plot(fpr * 100, fnr * 100, linewidth=2)
    plt.xlabel('False Positive Rate (%)')
    plt.ylabel('False Negative Rate (%)')
    plt.title('DET Curve')
    plt.grid(True, alpha=0.3)
    plt.xlim([0, 100])
    plt.ylim([0, 100])

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"DET curve saved to {output_path}")
    else:
        plt.show()

    plt.close()


def plot_score_distributions(genuine_scores: np.ndarray, spoof_scores: np.ndarray, output_path: str = None):
    """
    Plot score distributions for genuine and spoof

    Args:
        genuine_scores: Scores for genuine samples
        spoof_scores: Scores for spoof samples
        output_path: Optional path to save plot
    """
    plt.figure(figsize=(10, 6))

    plt.hist(genuine_scores, bins=50, alpha=0.6, label='Genuine', color='blue', density=True)
    plt.hist(spoof_scores, bins=50, alpha=0.6, label='Spoof', color='red', density=True)

    plt.xlabel('Spoof Score')
    plt.ylabel('Density')
    plt.title('Score Distributions')
    plt.legend()
    plt.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Score distribution plot saved to {output_path}")
    else:
        plt.show()

    plt.close()
