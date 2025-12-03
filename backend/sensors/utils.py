import io
import logging
import numpy as np
import soundfile as sf
import librosa
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def load_and_preprocess_audio(file_obj: io.BytesIO, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Load audio from a file object, convert to mono float32, and resample if necessary.
    
    Args:
        file_obj: BytesIO object containing audio data
        target_sr: Target sample rate in Hz (default 16000)
        
    Returns:
        Tuple of (audio_data, sample_rate)
        audio_data is a float32 mono numpy array
    """
    try:
        # Load audio using soundfile first (faster)
        file_obj.seek(0)
        audio, sr = sf.read(file_obj)
        
        # Convert to float32 if not already
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
            
        # Resample if necessary
        if sr != target_sr:
            # Use librosa for high-quality resampling
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
            
        return audio, sr
        
    except Exception as e:
        logger.error(f"Error loading audio: {e}")
        # Fallback or re-raise depending on requirements
        raise ValueError(f"Failed to process audio file: {e}")

def get_db_level(audio: np.ndarray) -> float:
    """Calculate dB level of audio signal."""
    rms = np.sqrt(np.mean(audio**2))
    if rms == 0:
        return -100.0
    return 20 * np.log10(rms)
