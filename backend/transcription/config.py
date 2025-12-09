"""
Transcription Configuration

Configuration settings for transcription providers and processing.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionConfig:
    """Configuration for transcription module."""
    
    # General settings
    enabled: bool = True
    demo_mode: bool = True
    default_provider: str = "whisper_local"
    default_language: str = "en"
    
    # Audio processing limits
    max_audio_size_mb: int = 800
    max_duration_seconds: float = 7200  # 2 hours
    chunk_duration_seconds: float = 30.0  # For chunked processing
    sample_rate: int = 16000
    
    # Whisper local settings
    whisper_model_size: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu or cuda
    whisper_compute_type: str = "int8"  # int8, float16, float32
    whisper_batch_size: int = 16
    
    # OpenAI Whisper API settings
    openai_api_key: Optional[str] = None
    openai_model: str = "whisper-1"
    openai_timeout_seconds: int = 300
    
    # AssemblyAI settings
    assemblyai_api_key: Optional[str] = None
    assemblyai_timeout_seconds: int = 600
    
    # Diarization settings
    diarization_enabled: bool = False
    diarization_min_speakers: int = 1
    diarization_max_speakers: int = 10
    pyannote_auth_token: Optional[str] = None
    
    # Processing settings
    temp_dir: Optional[str] = None
    cleanup_temp_files: bool = True
    
    # Health check settings
    health_check_interval_seconds: int = 60
    auto_disable_on_failure: bool = True
    max_consecutive_failures: int = 3
    
    def __post_init__(self):
        """Load settings from environment variables."""
        # Demo mode
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        
        # Provider settings from environment
        self.default_provider = os.getenv("TRANSCRIPTION_PROVIDER", self.default_provider)
        self.default_language = os.getenv("TRANSCRIPTION_DEFAULT_LANGUAGE", self.default_language)
        
        # Whisper settings
        self.whisper_model_size = os.getenv("WHISPER_MODEL_SIZE", self.whisper_model_size)
        self.whisper_device = os.getenv("WHISPER_DEVICE", self.whisper_device)
        
        # API keys from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY", self.assemblyai_api_key)
        self.pyannote_auth_token = os.getenv("PYANNOTE_AUTH_TOKEN", self.pyannote_auth_token)
        
        # Diarization settings
        diarization_env = os.getenv("TRANSCRIPTION_DIARIZATION_ENABLED", "").lower()
        if diarization_env:
            self.diarization_enabled = diarization_env == "true"
        
        # Temp directory
        self.temp_dir = os.getenv("TRANSCRIPTION_TEMP_DIR", self.temp_dir)
        
        logger.info(f"TranscriptionConfig initialized: provider={self.default_provider}, "
                   f"demo_mode={self.demo_mode}, diarization={self.diarization_enabled}")
    
    @property
    def max_audio_size_bytes(self) -> int:
        """Maximum audio size in bytes."""
        return self.max_audio_size_mb * 1024 * 1024
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available (has required keys/models)."""
        if provider == "demo":
            return True
        
        if provider == "whisper_local":
            # Local Whisper is always available (though may need model download)
            return True
        
        if provider == "whisper_api":
            return bool(self.openai_api_key)
        
        if provider == "assemblyai":
            return bool(self.assemblyai_api_key)
        
        return False
    
    def get_available_providers(self) -> list:
        """Get list of available providers."""
        providers = ["demo"]  # Demo is always available
        
        if self.is_provider_available("whisper_local"):
            providers.append("whisper_local")
        
        if self.is_provider_available("whisper_api"):
            providers.append("whisper_api")
        
        if self.is_provider_available("assemblyai"):
            providers.append("assemblyai")
        
        return providers
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "enabled": self.enabled,
            "demo_mode": self.demo_mode,
            "default_provider": self.default_provider,
            "default_language": self.default_language,
            "max_audio_size_mb": self.max_audio_size_mb,
            "max_duration_seconds": self.max_duration_seconds,
            "whisper_model_size": self.whisper_model_size,
            "whisper_device": self.whisper_device,
            "diarization_enabled": self.diarization_enabled,
            "available_providers": self.get_available_providers(),
            # Don't include API keys
            "has_openai_key": bool(self.openai_api_key),
            "has_assemblyai_key": bool(self.assemblyai_api_key),
            "has_pyannote_token": bool(self.pyannote_auth_token),
        }


# Singleton instance
_config: Optional[TranscriptionConfig] = None


def get_transcription_config() -> TranscriptionConfig:
    """Get the transcription configuration singleton."""
    global _config
    if _config is None:
        _config = TranscriptionConfig()
    return _config


def reset_config() -> None:
    """Reset the configuration singleton (for testing)."""
    global _config
    _config = None
