"""
Threshold optimization logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of a threshold optimization run."""
    sensor_name: str
    optimal_threshold: float
    eer: float  # Equal Error Rate
    auc: float  # Area Under Curve
    threshold_type: str  # "min" or "max"


class ThresholdOptimizer:
    """
    Optimizes sensor thresholds to minimize Equal Error Rate (EER).
    """

    def __init__(self, sensor_name: str):
        self.sensor_name = sensor_name

    def optimize(
        self,
        scores_real: List[float],
        scores_fake: List[float],
        search_range: Tuple[float, float],
        steps: int = 100
    ) -> OptimizationResult:
        """
        Find optimal threshold separating real and fake scores.
        
        Args:
            scores_real: List of scores for real audio
            scores_fake: List of scores for fake audio
            search_range: (min, max) range to search for threshold
            steps: Number of steps in search range
            
        Returns:
            OptimizationResult with optimal threshold and metrics
        """
        # Brute-force sweep to find threshold minimizing EER (Equal Error Rate)
        
        real = np.array(scores_real)
        fake = np.array(scores_fake)
        
        if len(real) == 0 or len(fake) == 0:
            logger.warning(f"Insufficient data for {self.sensor_name} optimization.")
            return OptimizationResult(self.sensor_name, 0.0, 0.0, 0.0, "unknown")

        # Determine if higher score means REAL or FAKE
        # Convention: We assume higher score = FAKE (e.g. error, diff, distance)
        # But if mean(real) > mean(fake), then higher = REAL.
        # We need to autodetect direction.
        mean_real = np.mean(real)
        mean_fake = np.mean(fake)
        
        higher_is_fake = mean_fake > mean_real
        
        # Define search range
        min_val = min(np.min(real), np.min(fake))
        max_val = max(np.max(real), np.max(fake))
        
        # Add slight padding
        padding = (max_val - min_val) * 0.05
        thresholds = np.linspace(min_val - padding, max_val + padding, steps)
        
        best_eer = 1.0
        best_threshold = 0.0
        
        for thresh in thresholds:
            if higher_is_fake:
                # FAKE if score > thresh
                # FAR (False Accept): Fake classified as Real (fake < thresh)
                # FRR (False Reject): Real classified as Fake (real > thresh)
                far = np.mean(fake < thresh)
                frr = np.mean(real > thresh)
            else:
                # FAKE if score < thresh
                # FAR: Fake classified as Real (fake > thresh)
                # FRR: Real classified as Fake (real < thresh)
                far = np.mean(fake > thresh)
                frr = np.mean(real < thresh)
            
            # EER is where FAR == FRR
            # To minimize error, we minimize the difference |FAR - FRR|
            # (or simplified: average error rate)
            current_eer = max(far, frr) # Approximate worst case error
            diff = abs(far - frr)
            
            # Weighted metric: closer FAR/FRR is better
            metric = diff + current_eer 
            
            if diff < best_eer:
                best_eer = diff
                best_threshold = thresh
        
        # Calculate final metrics at best threshold
        if higher_is_fake:
             far = np.mean(fake < best_threshold)
             frr = np.mean(real > best_threshold)
        else:
             far = np.mean(fake > best_threshold)
             frr = np.mean(real < best_threshold)
             
        final_eer = (far + frr) / 2.0
        
        return OptimizationResult(
            sensor_name=self.sensor_name,
            optimal_threshold=float(best_threshold),
            eer=float(final_eer),
            auc=0.0, # Placeholder, AUC calc requires sklearn
            threshold_type="max" if higher_is_fake else "min"
        )
