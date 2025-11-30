"""
Audio Processing Utilities

Functions for loading, preprocessing, and manipulating audio data.
"""

import os
import tempfile
import logging
from typing import Tuple, Union
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SAMPLE_RATE = 16000
MAX_FILE_SIZE_MB = 800
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def load_audio(
    source: Union[str, bytes, Path],
    target_sr: int = DEFAULT_SAMPLE_RATE,
    mono: bool = True,
) -> Tuple[np.ndarray, int]:
    """
    Load audio from file path or bytes.

    Args:
        source: File path, bytes, or Path object
        target_sr: Target sample rate for resampling
        mono: Whether to convert to mono

    Returns:
        Tuple of (audio array, sample rate)

    Raises:
        ValueError: If audio cannot be loaded or exceeds size limit
    """
    try:
        if isinstance(source, bytes):
            return _load_from_bytes(source, target_sr, mono)
        else:
            return _load_from_file(str(source), target_sr, mono)
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise ValueError(f"Failed to load audio: {e}")


def _load_from_file(file_path: str, target_sr: int, mono: bool) -> Tuple[np.ndarray, int]:
    """Load audio from file path."""
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"Audio file not found: {file_path}")

    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Audio file too large: {file_size / 1024 / 1024:.1f}MB "
            f"(max: {MAX_FILE_SIZE_MB}MB)"
        )

    audio, sr = librosa.load(file_path, sr=target_sr, mono=mono)
    return audio, sr


def _load_from_bytes(
    audio_bytes: bytes, target_sr: int, mono: bool
) -> Tuple[np.ndarray, int]:
    """Load audio from bytes using secure temporary file."""
    if len(audio_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Audio data too large: {len(audio_bytes) / 1024 / 1024:.1f}MB "
            f"(max: {MAX_FILE_SIZE_MB}MB)"
        )

    # Create secure temporary file
    fd = None
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.write(fd, audio_bytes)
        os.close(fd)
        fd = None  # Mark as closed

        audio, sr = librosa.load(temp_path, sr=target_sr, mono=mono)
        return audio, sr
    finally:
        # Clean up
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as e:
                logger.warning(f"Failed to remove temp file: {e}")


def preprocess_audio(
    audio: np.ndarray,
    sr: int = DEFAULT_SAMPLE_RATE,
    normalize: bool = True,
    trim: bool = True,
    top_db: int = 20,
) -> np.ndarray:
    """
    Preprocess audio for detection pipeline.

    Args:
        audio: Input audio array
        sr: Sample rate
        normalize: Whether to normalize amplitude
        trim: Whether to trim silence
        top_db: Threshold for silence trimming (dB)

    Returns:
        Preprocessed audio array
    """
    if audio is None or len(audio) == 0:
        raise ValueError("Empty audio data")

    processed = audio.astype(np.float32)

    if trim:
        processed = trim_silence(processed, top_db=top_db)

    if normalize:
        processed = normalize_audio(processed)

    return processed


def normalize_audio(audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    """
    Normalize audio to target dB level.

    Args:
        audio: Input audio array
        target_db: Target peak dB level

    Returns:
        Normalized audio array
    """
    if audio is None or len(audio) == 0:
        return audio

    # Compute peak amplitude
    peak = np.max(np.abs(audio))
    if peak == 0:
        return audio

    # Convert target_db to linear scale
    target_peak = 10 ** (target_db / 20.0)

    # Scale audio
    scale = target_peak / peak
    return audio * scale


def trim_silence(
    audio: np.ndarray, top_db: int = 20, frame_length: int = 2048, hop_length: int = 512
) -> np.ndarray:
    """
    Trim leading and trailing silence from audio.

    Args:
        audio: Input audio array
        top_db: Threshold below reference to consider as silence
        frame_length: Frame length for RMS computation
        hop_length: Hop length for RMS computation

    Returns:
        Trimmed audio array
    """
    if audio is None or len(audio) == 0:
        return audio

    trimmed, _ = librosa.effects.trim(
        audio, top_db=top_db, frame_length=frame_length, hop_length=hop_length
    )
    return trimmed


def get_audio_duration(audio: np.ndarray, sr: int = DEFAULT_SAMPLE_RATE) -> float:
    """
    Get audio duration in seconds.

    Args:
        audio: Audio array
        sr: Sample rate

    Returns:
        Duration in seconds
    """
    if audio is None or len(audio) == 0:
        return 0.0
    return len(audio) / sr


def resample_audio(
    audio: np.ndarray, orig_sr: int, target_sr: int = DEFAULT_SAMPLE_RATE
) -> np.ndarray:
    """
    Resample audio to target sample rate.

    Args:
        audio: Input audio array
        orig_sr: Original sample rate
        target_sr: Target sample rate

    Returns:
        Resampled audio array
    """
    if orig_sr == target_sr:
        return audio

    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def chunk_audio(
    audio: np.ndarray, chunk_size: int, overlap: int = 0
) -> list:
    """
    Split audio into overlapping chunks.

    Args:
        audio: Input audio array
        chunk_size: Size of each chunk in samples
        overlap: Overlap between chunks in samples

    Returns:
        List of audio chunks
    """
    if len(audio) <= chunk_size:
        return [audio]

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(audio) - overlap, step):
        end = min(start + chunk_size, len(audio))
        chunks.append(audio[start:end])
        if end == len(audio):
            break

    return chunks


def save_audio(
    audio: np.ndarray, file_path: str, sr: int = DEFAULT_SAMPLE_RATE
) -> None:
    """
    Save audio to file.

    Args:
        audio: Audio array to save
        file_path: Output file path
        sr: Sample rate
    """
    sf.write(file_path, audio, sr)
    logger.debug(f"Saved audio to {file_path}")
