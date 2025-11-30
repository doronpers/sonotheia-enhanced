"""
Test data generators for audio and signal processing.

Provides factories for creating synthetic test data.
"""

from dataclasses import dataclass
from typing import Optional, Literal
import io

# Try to import optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False


@dataclass
class AudioSpec:
    """
    Immutable audio specification.
    
    Attributes:
        duration_seconds: Length of audio in seconds
        samplerate: Sample rate in Hz
        num_channels: Number of audio channels
        dtype: Data type for audio samples
    
    Example:
        spec = AudioSpec(duration_seconds=2.0, samplerate=16000, num_channels=1)
    """
    duration_seconds: float
    samplerate: int
    num_channels: int = 1
    dtype: str = "float32"


class AudioGenerator:
    """
    Factory for generating synthetic audio test data.
    
    Hybrid design: OOP structure with static pure functions.
    
    Example:
        gen = AudioGenerator(default_samplerate=16000)
        
        # Generate signals
        sine = gen.sine_wave(frequency=440, duration_seconds=1.0, samplerate=16000)
        noise = gen.white_noise(duration_seconds=2.0, samplerate=16000, seed=42)
        
        # Convert to uploadable format
        audio_bytes = gen.to_bytes(sine, samplerate=16000, format='wav')
    """
    
    def __init__(self, default_samplerate: int = 16000):
        """
        Initialize generator with default sample rate.
        
        Args:
            default_samplerate: Default sample rate for generated audio
        """
        self._default_samplerate = default_samplerate
        
        if not HAS_NUMPY:
            raise ImportError("numpy is required for AudioGenerator. Install with: pip install numpy")
    
    @staticmethod
    def sine_wave(
        frequency: float,
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 0.5,
    ):
        """
        Generate a sine wave signal.
        
        Pure function for creating pure tone audio.
        
        Args:
            frequency: Frequency in Hz
            duration_seconds: Duration in seconds
            samplerate: Sample rate in Hz
            amplitude: Signal amplitude (0.0 to 1.0)
        
        Returns:
            numpy array of float32 samples
        
        Example:
            audio = AudioGenerator.sine_wave(440, 2.0, 16000)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required")
        
        t = np.linspace(
            0, duration_seconds,
            int(duration_seconds * samplerate),
            endpoint=False,
            dtype=np.float32,
        )
        return (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    
    @staticmethod
    def white_noise(
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 0.3,
        seed: Optional[int] = None,
    ):
        """
        Generate white noise.
        
        Pure function with optional seed for reproducibility.
        
        Args:
            duration_seconds: Duration in seconds
            samplerate: Sample rate in Hz
            amplitude: Signal amplitude
            seed: Random seed for reproducibility
        
        Returns:
            numpy array of float32 samples
        
        Example:
            noise = AudioGenerator.white_noise(1.0, 16000, seed=42)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required")
        
        if seed is not None:
            np.random.seed(seed)
        
        samples = int(duration_seconds * samplerate)
        return (amplitude * np.random.randn(samples)).astype(np.float32)
    
    @staticmethod
    def silence(duration_seconds: float, samplerate: int):
        """
        Generate silence (zeros).
        
        Args:
            duration_seconds: Duration in seconds
            samplerate: Sample rate in Hz
        
        Returns:
            numpy array of zeros
        
        Example:
            audio = AudioGenerator.silence(0.5, 16000)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required")
        
        samples = int(duration_seconds * samplerate)
        return np.zeros(samples, dtype=np.float32)
    
    @staticmethod
    def impulse_train(
        interval_seconds: float,
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 1.0,
    ):
        """
        Generate an impulse train (for testing high crest factor).
        
        Args:
            interval_seconds: Time between impulses
            duration_seconds: Total duration
            samplerate: Sample rate in Hz
            amplitude: Impulse amplitude
        
        Returns:
            numpy array with periodic impulses
        
        Example:
            impulses = AudioGenerator.impulse_train(0.1, 1.0, 16000)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required")
        
        samples = int(duration_seconds * samplerate)
        interval_samples = int(interval_seconds * samplerate)
        
        audio = np.zeros(samples, dtype=np.float32)
        if interval_samples > 0:
            audio[::interval_samples] = amplitude
        return audio
    
    @staticmethod
    def chirp(
        f_start: float,
        f_end: float,
        duration_seconds: float,
        samplerate: int,
        amplitude: float = 0.5,
    ):
        """
        Generate a frequency sweep (chirp).
        
        Args:
            f_start: Starting frequency in Hz
            f_end: Ending frequency in Hz
            duration_seconds: Duration in seconds
            samplerate: Sample rate in Hz
            amplitude: Signal amplitude
        
        Returns:
            numpy array with linear frequency sweep
        
        Example:
            sweep = AudioGenerator.chirp(100, 1000, 2.0, 16000)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required")
        
        samples = int(duration_seconds * samplerate)
        t = np.linspace(0, duration_seconds, samples, dtype=np.float32)
        
        # Linear frequency sweep
        frequency = f_start + (f_end - f_start) * t / duration_seconds
        phase = 2 * np.pi * np.cumsum(frequency) / samplerate
        
        return (amplitude * np.sin(phase)).astype(np.float32)
    
    def to_bytes(
        self,
        audio_data,
        samplerate: Optional[int] = None,
        format: Literal["wav", "flac", "ogg"] = "wav",
    ) -> io.BytesIO:
        """
        Convert audio array to bytes for upload testing.
        
        Args:
            audio_data: numpy array of audio samples
            samplerate: Sample rate (uses default if not provided)
            format: Output format
        
        Returns:
            BytesIO buffer containing audio file
        
        Example:
            audio_bytes = gen.to_bytes(audio_data, format='wav')
        """
        if not HAS_SOUNDFILE:
            raise ImportError("soundfile is required. Install with: pip install soundfile")
        
        buffer = io.BytesIO()
        sr = samplerate or self._default_samplerate
        sf.write(buffer, audio_data, sr, format=format)
        buffer.seek(0)
        return buffer
    
    def create_test_audio(
        self,
        spec: AudioSpec,
        signal_type: Literal["sine", "noise", "silence", "impulse", "chirp"] = "sine",
        **kwargs,
    ):
        """
        Factory method for creating test audio based on specification.
        
        Args:
            spec: AudioSpec defining audio properties
            signal_type: Type of signal to generate
            **kwargs: Additional parameters for signal generation
        
        Returns:
            numpy array of audio samples
        
        Example:
            spec = AudioSpec(duration_seconds=2.0, samplerate=16000)
            audio = gen.create_test_audio(spec, signal_type='sine', frequency=440)
        """
        generators = {
            "sine": lambda: self.sine_wave(
                kwargs.get("frequency", 440.0),
                spec.duration_seconds,
                spec.samplerate,
            ),
            "noise": lambda: self.white_noise(
                spec.duration_seconds,
                spec.samplerate,
                seed=kwargs.get("seed"),
            ),
            "silence": lambda: self.silence(
                spec.duration_seconds,
                spec.samplerate,
            ),
            "impulse": lambda: self.impulse_train(
                kwargs.get("interval", 0.1),
                spec.duration_seconds,
                spec.samplerate,
            ),
            "chirp": lambda: self.chirp(
                kwargs.get("f_start", 100),
                kwargs.get("f_end", 1000),
                spec.duration_seconds,
                spec.samplerate,
            ),
        }
        
        if signal_type not in generators:
            raise ValueError(f"Unknown signal type: {signal_type}")
        
        return generators[signal_type]()
