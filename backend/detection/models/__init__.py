"""
Detection Models

Neural network models for audio deepfake detection.
"""

from .rawnet3 import RawNet3, RawNet3Detector

__all__ = ["RawNet3", "RawNet3Detector"]
