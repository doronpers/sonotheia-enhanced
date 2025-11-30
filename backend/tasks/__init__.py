"""
Async Tasks Package

See _example_checks.txt for patterns on respecting module state in Celery tasks.
"""
Celery Tasks Package
Async task definitions for audio processing, detection, analysis, and SAR generation.
"""

from tasks.audio_tasks import process_audio, extract_features
from tasks.detection_tasks import detect_deepfake, detect_spoof
from tasks.analysis_tasks import analyze_call_async, run_full_analysis
from tasks.sar_tasks import generate_sar_async

__all__ = [
    "process_audio",
    "extract_features",
    "detect_deepfake",
    "detect_spoof",
    "analyze_call_async",
    "run_full_analysis",
    "generate_sar_async",
]
