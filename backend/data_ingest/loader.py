"""
Data Ingest Module - Loading WAV files and metadata

This module handles loading audio files and associated metadata for the Sonotheia MVP.
"""

import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class AudioLoader:
    """Load and preprocess audio files"""

    def __init__(self, target_sr: int = 16000):
        """
        Initialize audio loader

        Args:
            target_sr: Target sample rate for all audio (default 16kHz)
        """
        self.target_sr = target_sr

    def load_wav(self, file_path: str, sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """
        Load a WAV file and resample to target sample rate

        Args:
            file_path: Path to WAV file
            sr: Target sample rate (uses self.target_sr if None)

        Returns:
            Tuple of (audio array, sample rate)
        """
        sr = sr or self.target_sr

        try:
            # Load audio file
            audio, original_sr = sf.read(file_path)

            # Convert stereo to mono if needed
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Resample if needed
            if original_sr != sr:
                audio = librosa.resample(audio, orig_sr=original_sr, target_sr=sr)

            # Normalize to [-1, 1]
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0

            logger.info(f"Loaded audio: {file_path}, duration={len(audio)/sr:.2f}s, sr={sr}")

            return audio, sr

        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            raise

    def load_from_bytes(self, audio_bytes: bytes, sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """
        Load audio from byte array

        Args:
            audio_bytes: Audio data as bytes
            sr: Target sample rate

        Returns:
            Tuple of (audio array, sample rate)
        """
        import io
        sr = sr or self.target_sr

        try:
            # Load from bytes
            audio, original_sr = sf.read(io.BytesIO(audio_bytes))

            # Convert stereo to mono
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Resample
            if original_sr != sr:
                audio = librosa.resample(audio, orig_sr=original_sr, target_sr=sr)

            return audio, sr

        except Exception as e:
            logger.error(f"Error loading audio from bytes: {str(e)}")
            raise

    def save_wav(self, audio: np.ndarray, file_path: str, sr: Optional[int] = None):
        """
        Save audio to WAV file

        Args:
            audio: Audio array
            file_path: Output file path
            sr: Sample rate (uses self.target_sr if None)
        """
        sr = sr or self.target_sr

        try:
            sf.write(file_path, audio, sr)
            logger.info(f"Saved audio to {file_path}")
        except Exception as e:
            logger.error(f"Error saving {file_path}: {str(e)}")
            raise


class MetadataLoader:
    """Load and manage metadata for audio files"""

    @staticmethod
    def load_metadata(metadata_path: str) -> Dict[str, Any]:
        """
        Load metadata from JSON file

        Args:
            metadata_path: Path to metadata JSON file

        Returns:
            Dictionary with metadata
        """
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            logger.error(f"Error loading metadata from {metadata_path}: {str(e)}")
            raise

    @staticmethod
    def load_dataset_metadata(dataset_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        Load metadata for all files in a dataset

        Args:
            dataset_dir: Directory containing audio files and metadata

        Returns:
            Dictionary mapping file IDs to metadata
        """
        metadata_file = Path(dataset_dir) / "metadata.json"

        if metadata_file.exists():
            return MetadataLoader.load_metadata(str(metadata_file))

        # If no metadata file, scan for audio files
        logger.warning(f"No metadata.json found in {dataset_dir}, scanning for audio files")

        audio_files = list(Path(dataset_dir).glob("*.wav"))
        metadata = {}

        for audio_file in audio_files:
            file_id = audio_file.stem
            metadata[file_id] = {
                "file_path": str(audio_file),
                "file_id": file_id
            }

        return metadata
