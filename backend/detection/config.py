"""
Detection Pipeline Configuration

Configuration settings for the 6-stage detection pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import yaml
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeatureExtractionConfig:
    """Configuration for Stage 1: Feature Extraction"""

    sample_rate: int = 16000
    n_fft: int = 512
    hop_length: int = 160
    win_length: int = 400
    n_mfcc: int = 20
    n_lfcc: int = 20
    n_cqcc: int = 20
    feature_types: List[str] = field(default_factory=lambda: ["mfcc", "lfcc", "logspec"])
    include_deltas: bool = True


@dataclass
class TemporalAnalysisConfig:
    """Configuration for Stage 2: Temporal Analysis"""

    window_size: int = 100  # frames
    hop_size: int = 50  # frames
    min_segment_length: int = 10  # frames
    smoothing_window: int = 5
    threshold_std_multiplier: float = 2.0


@dataclass
class ArtifactDetectionConfig:
    """Configuration for Stage 3: Artifact Detection"""

    # Silence detection
    silence_threshold_db: float = -40.0
    min_silence_duration: float = 0.1  # seconds

    # Click/pop detection
    click_threshold: float = 0.8
    click_min_gap: int = 100  # samples

    # Frequency artifact detection
    artifact_frequency_bands: List[tuple] = field(
        default_factory=lambda: [
            (0, 100),  # Sub-bass artifacts
            (8000, 16000),  # High frequency artifacts
        ]
    )


@dataclass
class RawNet3Config:
    """Configuration for Stage 4: RawNet3 Neural Network"""

    model_path: Optional[str] = None
    device: str = "auto"  # "cpu", "cuda", or "auto"
    batch_size: int = 1
    use_half_precision: bool = False
    cache_model: bool = True

    # Architecture params
    sinc_out_channels: int = 128
    sinc_kernel_size: int = 251
    encoder_type: str = "ResNet34"
    attention_heads: int = 8


@dataclass
class FusionEngineConfig:
    """Configuration for Stage 5: Dual-Branch Fusion"""

    fusion_method: str = "weighted_average"  # "weighted_average", "max", "learned"
    stage_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "feature_extraction": 0.15,
            "temporal_analysis": 0.15,
            "artifact_detection": 0.15,
            "rawnet3": 0.40,
            "explainability": 0.15,
        }
    )
    confidence_threshold: float = 0.5
    decision_threshold: float = 0.5


@dataclass
class ExplainabilityConfig:
    """Configuration for Stage 6: Explainability"""

    generate_saliency: bool = True
    include_feature_importance: bool = True
    include_temporal_segments: bool = True
    max_top_features: int = 10
    explanation_detail_level: str = "standard"  # "minimal", "standard", "detailed"
    llm_model_id: str = "meta-llama/Meta-Llama-3-70B-Instruct"
    enable_llm: bool = True


@dataclass
class PhysicsAnalysisConfig:
    """Configuration for Stage 3b: Physics Analysis"""
    enabled: bool = True


@dataclass
class DetectionConfig:
    """Main detection pipeline configuration."""

    # Demo mode (uses placeholder logic)
    demo_mode: bool = True

    # Stage configurations
    feature_extraction: FeatureExtractionConfig = field(
        default_factory=FeatureExtractionConfig
    )
    temporal_analysis: TemporalAnalysisConfig = field(
        default_factory=TemporalAnalysisConfig
    )
    artifact_detection: ArtifactDetectionConfig = field(
        default_factory=ArtifactDetectionConfig
    )
    rawnet3: RawNet3Config = field(default_factory=RawNet3Config)
    fusion_engine: FusionEngineConfig = field(default_factory=FusionEngineConfig)

    physics_analysis: PhysicsAnalysisConfig = field(default_factory=PhysicsAnalysisConfig)
    explainability: ExplainabilityConfig = field(default_factory=ExplainabilityConfig)

    # Pipeline settings
    enable_caching: bool = True
    max_audio_duration: float = 300.0  # seconds
    min_audio_duration: float = 0.5  # seconds
    timeout_seconds: float = 120.0

    # Quick detection mode (stages 1-3 only)
    quick_mode_stages: List[str] = field(
        default_factory=lambda: [
            "feature_extraction",
            "temporal_analysis",
            "artifact_detection",
        ]
    )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "DetectionConfig":
        """Load configuration from YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetectionConfig":
        """Create configuration from dictionary."""
        config = cls()

        if "demo_mode" in data:
            config.demo_mode = data["demo_mode"]

        if "feature_extraction" in data:
            for key, value in data["feature_extraction"].items():
                if hasattr(config.feature_extraction, key):
                    setattr(config.feature_extraction, key, value)

        if "temporal_analysis" in data:
            for key, value in data["temporal_analysis"].items():
                if hasattr(config.temporal_analysis, key):
                    setattr(config.temporal_analysis, key, value)

        if "artifact_detection" in data:
            for key, value in data["artifact_detection"].items():
                if hasattr(config.artifact_detection, key):
                    setattr(config.artifact_detection, key, value)

        if "rawnet3" in data:
            for key, value in data["rawnet3"].items():
                if hasattr(config.rawnet3, key):
                    setattr(config.rawnet3, key, value)

        if "fusion_engine" in data:
            for key, value in data["fusion_engine"].items():
                if hasattr(config.fusion_engine, key):
                    setattr(config.fusion_engine, key, value)

        if "explainability" in data:
            for key, value in data["explainability"].items():
                if hasattr(config.explainability, key):
                    setattr(config.explainability, key, value)

        if "physics_analysis" in data:
            for key, value in data["physics_analysis"].items():
                if hasattr(config.physics_analysis, key):
                    setattr(config.physics_analysis, key, value)

        for key in ["enable_caching", "max_audio_duration", "min_audio_duration", "timeout_seconds"]:
            if key in data:
                setattr(config, key, data[key])

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict

        return asdict(self)


def get_default_config() -> DetectionConfig:
    """Get default detection configuration."""
    # Check for environment-based demo mode
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
    config = DetectionConfig(demo_mode=demo_mode)

    # Check for config file
    config_paths = [
        Path(__file__).parent.parent / "config" / "detection.yaml",
        Path(__file__).parent.parent.parent / "config" / "detection.yaml",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                config = DetectionConfig.from_yaml(str(config_path))
                logger.info(f"Loaded detection config from {config_path}")
                break
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

    return config
