"""
Sensor module for physics-based audio analysis.

This module provides a modular, object-oriented architecture for audio sensors.
All sensors inherit from BaseSensor and implement the analyze() method.

Optionally uses high-performance Rust implementations when available.
"""

# Try to import Rust accelerated functions
# Falls back to scipy/numpy if Rust module is not available
try:
    from sonotheia_rust import (
        compute_fft,
        extract_spectral_features,
        compute_spectral_rolloff,
        compute_rms,
        compute_zero_crossing_rate,
        compute_crest_factor,
    )
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    # Rust module not available - sensors will use scipy/numpy fallback
    compute_fft = None
    extract_spectral_features = None
    compute_spectral_rolloff = None
    compute_rms = None
    compute_zero_crossing_rate = None
    compute_crest_factor = None

from .base import BaseSensor, SensorResult
from .breath import BreathSensor
from .breathing_pattern import BreathingPatternSensor
from .dynamic_range import DynamicRangeSensor
from .bandwidth import BandwidthSensor
from .phase_coherence import PhaseCoherenceSensor
from .glottal_inertia import GlottalInertiaSensor
from .digital_silence import DigitalSilenceSensor
from .global_formants import GlobalFormantSensor
from .coarticulation import CoarticulationSensor
from .formant import FormantTrajectorySensor
from .enf import ENFSensor
from .registry import SensorRegistry, get_default_sensors



# HuggingFace-based sensors (optional - requires transformers)
try:
    from .huggingface_detector import (
        HuggingFaceDetectorSensor,
        HuggingFaceSpeakerEmbedding,
        SUPPORTED_MODELS as HF_SUPPORTED_MODELS,
    )
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HuggingFaceDetectorSensor = None
    HuggingFaceSpeakerEmbedding = None
    HF_SUPPORTED_MODELS = {}
    HUGGINGFACE_AVAILABLE = False

__all__ = [
    "BaseSensor",
    "SensorResult",
    "BreathSensor",
    "BreathingPatternSensor",
    "DynamicRangeSensor",
    "BandwidthSensor",
    "PhaseCoherenceSensor",
    "GlottalInertiaSensor",
    "FormantTrajectorySensor",
    "GlobalFormantSensor",
    "ENFSensor",
    "CoarticulationSensor",
    "DigitalSilenceSensor",
    "ModelConfig",
    "ModelStatus",
    "SensorRegistry",
    "VoiceActivityDetector",
    "SpeechSegment",
    "RUST_AVAILABLE",
    "ONNX_AVAILABLE",
    "compute_fft",
    "extract_spectral_features",
    "compute_spectral_rolloff",
    "compute_rms",
    "compute_zero_crossing_rate",
    "compute_crest_factor",
    # HuggingFace exports
    "HuggingFaceDetectorSensor",
    "HuggingFaceSpeakerEmbedding",
    "HUGGINGFACE_AVAILABLE",
    "HF_SUPPORTED_MODELS",

]




