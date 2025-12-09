"""
Benchmark Harness for Sonotheia MVP

Run batch evaluation on a dataset of audio files with configurable parameters.
"""

import argparse
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys
import pandas as pd
import numpy as np

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingest.loader import AudioLoader
from telephony.pipeline import TelephonyPipeline
from features.extraction import FeatureExtractor
from models.baseline import GMMSpoofDetector
from evaluation.codec_experiments import run_multi_codec_experiment, print_results_table
from evaluation.metrics import compute_all_metrics, plot_roc_curve, plot_score_distributions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BenchmarkConfig:
    """Benchmark configuration"""

    def __init__(self, config_path: str):
        """Load config from YAML file"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.dataset_dir = self.config.get('dataset_dir', '.')
        self.metadata_file = self.config.get('metadata_file', 'metadata.csv')
        self.output_dir = self.config.get('output_dir', 'benchmark_results')
        self.model_path = self.config.get('model_path', None)

        # Feature extraction config
        self.feature_types = self.config.get('feature_types', ['lfcc', 'logspec'])
        self.sample_rate = self.config.get('sample_rate', 16000)

        # Codec config
        self.codecs = self.config.get('codecs', ['landline', 'mobile', 'voip', 'clean'])

        # Evaluation config
        self.eval_metrics = self.config.get('eval_metrics', True)
        self.generate_plots = self.config.get('generate_plots', True)


class BenchmarkRunner:
    """Run benchmark experiments"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.loader = AudioLoader(target_sr=config.sample_rate)
        self.telephony = TelephonyPipeline()
        self.feature_extractor = FeatureExtractor(sr=config.sample_rate)
        self.detector = GMMSpoofDetector()

        # Load model if available
        if config.model_path and Path(config.model_path).exists():
            self.detector.load(config.model_path)
            logger.info(f"Loaded model from {config.model_path}")
        else:
            logger.warning("No model loaded - will use placeholder scores")
            self.detector = None

    def load_dataset(self) -> tuple:
        """
        Load dataset from metadata file

        Returns:
            Tuple of (audio_paths, labels)
        """
        metadata_path = Path(self.config.dataset_dir) / self.config.metadata_file

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load metadata CSV
        df = pd.read_csv(metadata_path)

        # Expect columns: file_path, label (0=genuine, 1=spoof)
        if 'file_path' not in df.columns or 'label' not in df.columns:
            raise ValueError("Metadata CSV must contain 'file_path' and 'label' columns")

        # Get full paths
        audio_paths = [str(Path(self.config.dataset_dir) / p) for p in df['file_path']]
        labels = df['label'].tolist()

        logger.info(f"Loaded dataset: {len(audio_paths)} files")
        logger.info(f"Genuine: {sum(label == 0 for label in labels)}, Spoof: {sum(label == 1 for label in labels)}")

        return audio_paths, labels

    def run_codec_experiments(self, audio_paths: List[str], labels: List[int]) -> List[Dict]:
        """Run experiments across codec conditions"""

        # Create codec chains
        codec_chains = {}
        for codec_name in self.config.codecs:
            codec_chains[codec_name] = lambda audio, sr, cn=codec_name: (
                self.telephony.apply_codec_by_name(audio, sr, cn)
            )

        # Feature extraction function
        def extract_features(audio, sr):
            return self.feature_extractor.extract_feature_stack(
                audio,
                feature_types=self.config.feature_types
            )

        # Prediction function
        def predict_score(features):
            if self.detector:
                return self.detector.predict_score(features)
            else:
                # Placeholder
                return np.random.random()

        # Run experiments
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(self.config.output_dir) / f"codec_experiments_{timestamp}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        results = run_multi_codec_experiment(
            audio_paths=audio_paths,
            labels=labels,
            codec_chains=codec_chains,
            feature_extractor_fn=extract_features,
            model_predict_fn=predict_score,
            output_path=str(output_path)
        )

        # Print results table
        print_results_table(results)

        return results

    def run_full_evaluation(self, audio_paths: List[str], labels: List[int]):
        """Run full evaluation with metrics and plots"""

        logger.info("Running full evaluation...")

        # Use default codec (landline)
        scores = []

        for audio_path, label in zip(audio_paths, labels):
            try:
                # Load audio
                audio, sr = self.loader.load_wav(audio_path)

                # Apply codec
                audio_coded = self.telephony.apply_landline_chain(audio, sr)

                # Extract features
                features = self.feature_extractor.extract_feature_stack(
                    audio_coded,
                    feature_types=self.config.feature_types
                )

                # Predict score
                if self.detector:
                    score = self.detector.predict_score(features)
                else:
                    score = np.random.random()

                scores.append(score)

            except Exception as e:
                logger.error(f"Error processing {audio_path}: {e}")
                scores.append(0.5)

        scores = np.array(scores)
        labels = np.array(labels)

        # Compute metrics
        metrics = compute_all_metrics(labels, scores, threshold=0.5)

        logger.info("Evaluation Metrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")

        # Save metrics
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = output_dir / f"metrics_{timestamp}.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Metrics saved to {metrics_path}")

        # Generate plots
        if self.config.generate_plots:
            logger.info("Generating plots...")

            # ROC curve
            roc_path = output_dir / f"roc_curve_{timestamp}.png"
            plot_roc_curve(labels, scores, output_path=str(roc_path))

            # Score distributions
            genuine_scores = scores[labels == 0]
            spoof_scores = scores[labels == 1]

            dist_path = output_dir / f"score_distributions_{timestamp}.png"
            plot_score_distributions(genuine_scores, spoof_scores, output_path=str(dist_path))

        return metrics


def main():
    """Main benchmark script"""

    parser = argparse.ArgumentParser(description="Run Sonotheia MVP benchmark")
    parser.add_argument('config', type=str, help='Path to benchmark config YAML file')
    parser.add_argument('--codec-experiments', action='store_true', help='Run codec experiments')
    parser.add_argument('--full-eval', action='store_true', help='Run full evaluation with metrics')

    args = parser.parse_args()

    # Load config
    config = BenchmarkConfig(args.config)

    # Create runner
    runner = BenchmarkRunner(config)

    # Load dataset
    audio_paths, labels = runner.load_dataset()

    # Run experiments
    if args.codec_experiments:
        runner.run_codec_experiments(audio_paths, labels)

    if args.full_eval:
        runner.run_full_evaluation(audio_paths, labels)

    if not args.codec_experiments and not args.full_eval:
        logger.info("No experiment type specified. Use --codec-experiments or --full-eval")
        logger.info("Running codec experiments by default...")
        runner.run_codec_experiments(audio_paths, labels)

    logger.info("Benchmark complete!")


if __name__ == "__main__":
    main()
