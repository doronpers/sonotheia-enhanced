"""
Calibration module for Sonotheia sensors.

Provides tools to:
1. Optimize sensor thresholds against labeled datasets.
2. Calibrate Likelihood Ratio (LR) models.
3. Generate performance reports (EER, AUC).
"""

from .optimizer import ThresholdOptimizer

__all__ = ["ThresholdOptimizer"]
