"""
Audio Deepfake Detection Pipeline

A comprehensive 6-stage detection pipeline for audio deepfake detection.

Stages:
1. Feature Extraction - MFCC, LFCC, spectral features
2. Temporal Analysis - Pattern and discontinuity detection
3. Artifact Detection - Click, silence, frequency artifacts
4. RawNet3 Neural - Deep learning detection
5. Fusion Engine - Multi-stage score fusion
6. Explainability - Human-readable explanations

Usage:
    from detection import DetectionPipeline

    # Initialize pipeline
    pipeline = DetectionPipeline()

    # Run detection
    result = pipeline.detect("audio.wav")

    # Or run quick detection (stages 1-3 only)
    result = pipeline.detect("audio.wav", quick_mode=True)
"""

from .pipeline import DetectionPipeline, DetectionJob, JobStatus, get_pipeline
from .config import DetectionConfig, get_default_config
from .utils import convert_numpy_types, load_audio, preprocess_audio

__all__ = [
    "DetectionPipeline",
    "DetectionJob",
    "JobStatus",
    "get_pipeline",
    "DetectionConfig",
    "get_default_config",
    "convert_numpy_types",
    "load_audio",
    "preprocess_audio",
]

__version__ = "1.0.0"
