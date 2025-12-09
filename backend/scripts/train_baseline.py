"""
Train Baseline Spoof Detection Model

Train GMM-based spoof detector on labeled audio dataset.
"""

import argparse
import logging
from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingest.loader import AudioLoader
from telephony.pipeline import TelephonyPipeline
from features.extraction import FeatureExtractor
from models.baseline import GMMSpoofDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_dataset(dataset_dir: str, metadata_file: str, codec: str = 'landline', max_samples: int = None):
    """
    Load and preprocess dataset

    Args:
        dataset_dir: Directory containing audio files
        metadata_file: CSV file with file_path and label columns
        codec: Codec to apply
        max_samples: Maximum samples to load (None = all)

    Returns:
        Tuple of (genuine_features, spoof_features)
    """
    # Load metadata
    metadata_path = Path(dataset_dir) / metadata_file
    df = pd.read_csv(metadata_path)

    if max_samples:
        df = df.sample(n=min(max_samples, len(df)), random_state=42)

    # Initialize components
    loader = AudioLoader(target_sr=16000)
    telephony = TelephonyPipeline()
    extractor = FeatureExtractor(sr=16000)

    genuine_features_list = []
    spoof_features_list = []

    for idx, row in df.iterrows():
        file_path = Path(dataset_dir) / row['file_path']
        label = row['label']

        try:
            # Load audio
            audio, sr = loader.load_wav(str(file_path))

            # Apply codec
            audio_coded = telephony.apply_codec_by_name(audio, sr, codec)

            # Extract features
            features = extractor.extract_feature_stack(audio_coded, feature_types=['lfcc', 'logspec'])

            # Separate by label
            if label == 0:
                genuine_features_list.append(features)
            else:
                spoof_features_list.append(features)

            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} files")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue

    # Concatenate all features
    genuine_features = np.vstack(genuine_features_list)
    spoof_features = np.vstack(spoof_features_list)

    logger.info(f"Loaded features - Genuine: {genuine_features.shape}, Spoof: {spoof_features.shape}")

    return genuine_features, spoof_features


def train_model(genuine_features, spoof_features, output_path: str, n_components: int = 32):
    """
    Train GMM spoof detector

    Args:
        genuine_features: Features from genuine samples
        spoof_features: Features from spoof samples
        output_path: Where to save trained model
        n_components: Number of GMM components
    """
    logger.info("Training GMM spoof detector...")

    # Create and train model
    detector = GMMSpoofDetector(n_components=n_components, random_state=42)
    detector.train(genuine_features, spoof_features)

    # Save model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    detector.save(str(output_path))
    logger.info(f"Model saved to {output_path}")

    return detector


def main():
    """Main training script"""
    parser = argparse.ArgumentParser(description="Train baseline spoof detection model")
    parser.add_argument('--dataset-dir', type=str, required=True, help='Dataset directory')
    parser.add_argument('--metadata-file', type=str, default='metadata.csv', help='Metadata CSV file')
    parser.add_argument('--codec', type=str, default='landline', choices=['landline', 'mobile', 'voip', 'clean'],
                        help='Codec to apply during training')
    parser.add_argument('--output', type=str, default='./models/gmm_spoof_detector.pkl',
                        help='Output model path')
    parser.add_argument('--n-components', type=int, default=32, help='Number of GMM components')
    parser.add_argument('--max-samples', type=int, default=None, help='Max samples to use (for testing)')

    args = parser.parse_args()

    logger.info("Training baseline spoof detector")
    logger.info(f"Dataset: {args.dataset_dir}")
    logger.info(f"Codec: {args.codec}")
    logger.info(f"GMM components: {args.n_components}")

    # Load dataset
    genuine_features, spoof_features = load_dataset(
        dataset_dir=args.dataset_dir,
        metadata_file=args.metadata_file,
        codec=args.codec,
        max_samples=args.max_samples
    )

    # Train model
    detector = train_model(
        genuine_features=genuine_features,
        spoof_features=spoof_features,
        output_path=args.output,
        n_components=args.n_components
    )

    logger.info("Training complete!")


if __name__ == "__main__":
    main()
