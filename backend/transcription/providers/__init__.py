"""
Transcription Providers Package

Abstraction layer for multiple transcription backends.
"""

from .base import TranscriptionProvider, TranscriptionError
from .demo import DemoProvider

__all__ = [
    "TranscriptionProvider",
    "TranscriptionError",
    "DemoProvider",
]


def get_provider(provider_name: str):
    """
    Factory function to get a transcription provider by name.
    
    Args:
        provider_name: Name of the provider ('whisper_local', 'whisper_api', 'assemblyai', 'demo')
    
    Returns:
        TranscriptionProvider instance
    
    Raises:
        ValueError: If provider name is invalid or unavailable
    """
    from ..config import get_transcription_config
    
    config = get_transcription_config()
    
    if provider_name == "demo":
        return DemoProvider(config)
    
    if provider_name == "whisper_local":
        from .whisper_local import WhisperLocalProvider
        return WhisperLocalProvider(config)
    
    if provider_name == "whisper_api":
        if not config.openai_api_key:
            raise ValueError("OpenAI API key not configured for whisper_api provider")
        from .whisper_api import WhisperAPIProvider
        return WhisperAPIProvider(config)
    
    if provider_name == "assemblyai":
        if not config.assemblyai_api_key:
            raise ValueError("AssemblyAI API key not configured")
        from .assemblyai import AssemblyAIProvider
        return AssemblyAIProvider(config)
    
    raise ValueError(f"Unknown transcription provider: {provider_name}")
