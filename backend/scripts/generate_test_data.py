"""
Generate minimal test dataset for pipeline testing

Creates synthetic audio files to test the pipeline without needing real data.
"""

import numpy as np
import soundfile as sf
from pathlib import Path
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_genuine_audio(duration: float = 2.0, sr: int = 16000) -> np.ndarray:
    """Generate realistic-sounding genuine speech-like audio"""
    t = np.linspace(0, duration, int(sr * duration))

    # Mix of formants (like speech)
    audio = (
        0.3 * np.sin(2 * np.pi * 150 * t) +  # F0 (fundamental)
        0.2 * np.sin(2 * np.pi * 750 * t) +  # F1 (formant 1)
        0.15 * np.sin(2 * np.pi * 1200 * t) + # F2 (formant 2)
        0.1 * np.sin(2 * np.pi * 2400 * t)    # F3 (formant 3)
    )

    # Add some variation (prosody)
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)
    audio = audio * envelope

    # Add realistic noise
    audio += 0.02 * np.random.randn(len(audio))

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.7

    return audio.astype(np.float32)


def generate_spoof_audio(duration: float = 2.0, sr: int = 16000) -> np.ndarray:
    """Generate synthetic/spoof audio with artifacts"""
    t = np.linspace(0, duration, int(sr * duration))

    # More mechanical/synthetic sounding
    audio = (
        0.4 * np.sin(2 * np.pi * 200 * t) +
        0.3 * np.sin(2 * np.pi * 800 * t) +
        0.2 * np.sin(2 * np.pi * 1600 * t) +
        0.1 * np.sin(2 * np.pi * 3200 * t)
    )

    # Add periodic artifacts (like vocoder)
    artifact = 0.1 * np.sin(2 * np.pi * 50 * t)
    audio += artifact

    # Less natural noise
    audio += 0.01 * np.random.randn(len(audio))

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.7

    return audio.astype(np.float32)


def create_test_dataset(output_dir: str, num_genuine: int = 10, num_spoof: int = 10):
    """Create complete test dataset with metadata"""

    output_path = Path(output_dir)
    genuine_dir = output_path / "genuine"
    spoof_dir = output_path / "spoof"

    genuine_dir.mkdir(parents=True, exist_ok=True)
    spoof_dir.mkdir(parents=True, exist_ok=True)

    metadata = []

    # Generate genuine samples
    logger.info(f"Generating {num_genuine} genuine samples...")
    for i in range(num_genuine):
        audio = generate_genuine_audio(duration=2.0 + np.random.random())
        filename = f"genuine_{i:03d}.wav"
        filepath = genuine_dir / filename
        sf.write(str(filepath), audio, 16000)

        metadata.append({
            'file_path': f"genuine/{filename}",
            'label': 0,
            'type': 'genuine',
            'duration': len(audio) / 16000
        })

    # Generate spoof samples
    logger.info(f"Generating {num_spoof} spoof samples...")
    for i in range(num_spoof):
        audio = generate_spoof_audio(duration=2.0 + np.random.random())
        filename = f"spoof_{i:03d}.wav"
        filepath = spoof_dir / filename
        sf.write(str(filepath), audio, 16000)

        metadata.append({
            'file_path': f"spoof/{filename}",
            'label': 1,
            'type': 'spoof',
            'duration': len(audio) / 16000
        })

    # Save metadata
    df = pd.DataFrame(metadata)
    metadata_path = output_path / "metadata.csv"
    df.to_csv(metadata_path, index=False)

    logger.info(f"Dataset created at {output_path}")
    logger.info(f"Total files: {len(metadata)}")
    logger.info(f"Metadata saved to {metadata_path}")

    return metadata_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate test dataset")
    parser.add_argument('--output-dir', type=str, default='./data/test_dataset',
                        help='Output directory')
    parser.add_argument('--num-genuine', type=int, default=10,
                        help='Number of genuine samples')
    parser.add_argument('--num-spoof', type=int, default=10,
                        help='Number of spoof samples')

    args = parser.parse_args()

    create_test_dataset(args.output_dir, args.num_genuine, args.num_spoof)

    logger.info("\n✓ Test dataset ready!")
    logger.info(f"  Location: {args.output_dir}")
    logger.info(f"  Genuine: {args.num_genuine} samples")
    logger.info(f"  Spoof: {args.num_spoof} samples")
