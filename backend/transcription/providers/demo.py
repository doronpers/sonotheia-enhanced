"""
Demo Transcription Provider

A mock provider for testing and demonstration purposes.
Returns synthetic transcription data without requiring actual models.
"""

import asyncio
import logging
from typing import Optional
import numpy as np

from .base import TranscriptionProvider, TranscriptionError
from ..models import Transcript

logger = logging.getLogger(__name__)


class DemoProvider(TranscriptionProvider):
    """Demo transcription provider for testing."""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "demo"
    
    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None,
        **kwargs
    ) -> Transcript:
        """
        Generate demo transcription.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            language: Optional language code
            **kwargs: Additional options including audio_id
        
        Returns:
            Demo Transcript with synthetic data
        """
        audio_id = kwargs.get('audio_id', 'demo-audio')
        
        # Calculate duration from audio data
        duration = len(audio_data) / sample_rate if sample_rate > 0 else 0
        duration = float(self._convert_numpy_to_native(duration))
        
        # Generate demo segments based on duration
        segments = self._generate_demo_segments(duration)
        
        # Simulate processing time
        await asyncio.sleep(min(duration * 0.1, 2.0))  # ~10% of duration, max 2 seconds
        
        language = language or "en"
        
        logger.info(f"Demo transcription completed for {audio_id}: {duration:.2f}s, {len(segments)} segments")
        
        self.mark_success()
        
        return self._create_transcript(
            audio_id=audio_id,
            segments=segments,
            language=language,
            duration=duration
        )
    
    async def is_available(self) -> bool:
        """Demo provider is always available."""
        return True
    
    def _generate_demo_segments(self, duration: float) -> list:
        """Generate demo transcript segments."""
        if duration <= 0:
            return []
        
        # Demo conversation segments
        demo_texts = [
            ("SPEAKER_00", "Hello, thank you for calling. How may I assist you today?"),
            ("SPEAKER_01", "Hi, I need to make a wire transfer to my business account."),
            ("SPEAKER_00", "I can help you with that. Can you please verify your account number?"),
            ("SPEAKER_01", "Yes, my account number is one two three four five six seven eight nine."),
            ("SPEAKER_00", "Thank you. What is the amount you'd like to transfer?"),
            ("SPEAKER_01", "I need to transfer fifty thousand dollars."),
            ("SPEAKER_00", "I understand. For security purposes, I'll need to verify your identity."),
            ("SPEAKER_01", "Of course, what information do you need?"),
            ("SPEAKER_00", "Could you please state your full name and date of birth?"),
            ("SPEAKER_01", "My name is John Smith and my date of birth is January 15, 1980."),
        ]
        
        segments = []
        current_time = 0.0
        segment_duration = duration / len(demo_texts) if duration > 0 else 3.0
        
        for i, (speaker, text) in enumerate(demo_texts):
            if current_time >= duration:
                break
            
            end_time = min(current_time + segment_duration, duration)
            
            segments.append({
                'start': current_time,
                'end': end_time,
                'text': text,
                'confidence': 0.95 - (i * 0.01),  # Slight variation
                'speaker': speaker
            })
            
            current_time = end_time
        
        return segments
