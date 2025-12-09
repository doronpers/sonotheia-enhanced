import io
import logging
import numpy as np
import soundfile as sf
import librosa
from typing import Tuple

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
    # Try soundfile first (faster, better for most formats)
    try:
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
        
    except Exception as sf_error:
        error_type = type(sf_error).__name__
        error_msg = str(sf_error) if sf_error else "Unknown error"
        logger.warning(f"soundfile failed ({error_type}: {error_msg}), trying librosa fallback...")
        
        # Fallback to librosa (handles corrupted files better in some cases)
        try:
            file_obj.seek(0)
            audio, sr = librosa.load(file_obj, sr=target_sr, mono=True, dtype=np.float32)
            logger.info(f"Successfully loaded audio using librosa fallback (sr={sr})")
            return audio, sr
        except Exception as librosa_error:
            error_type_final = type(librosa_error).__name__
            error_msg_final = str(librosa_error) if librosa_error else "Unknown error"
            logger.error(f"Both soundfile and librosa failed. Last error: {error_type_final}: {error_msg_final}")
            raise ValueError(f"Failed to process audio file: soundfile error ({error_type}: {error_msg}), librosa error ({error_type_final}: {error_msg_final})")

def get_db_level(audio: np.ndarray) -> float:
    """Calculate dB level of audio signal."""
    rms = np.sqrt(np.mean(audio**2))
    if rms == 0:
        return -100.0
    return 20 * np.log10(rms)
