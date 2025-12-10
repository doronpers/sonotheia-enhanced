"""
Calibration utility for ProsodicContinuitySensor.

This script analyzes organic (authentic) speech samples to learn the natural
baseline for prosodic breaks and establish appropriate thresholds.

Usage:
    python calibrate_prosodic.py --organic-dir /path/to/organic/samples [--output config.yaml]
    
The script will:
1. Analyze all organic speech samples
2. Compute statistics on prosodic breaks in natural speech
3. Suggest appropriate thresholds based on percentiles
4. Optionally output a config file with recommended settings
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys

import numpy as np
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensors.prosodic_continuity import ProsodicContinuitySensor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_audio(filepath: Path) -> tuple[np.ndarray, int]:
    """
    Load audio file using scipy or other available backend.
    
    Args:
        filepath: Path to audio file
        
    Returns:
        Tuple of (audio_data, samplerate)
    """
    try:
        from scipy.io import wavfile
        samplerate, audio_data = wavfile.read(filepath)
        
        # Convert to float and normalize
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        elif audio_data.dtype == np.uint8:
            audio_data = (audio_data.astype(np.float32) - 128) / 128.0
        
        # Convert stereo to mono if needed
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        return audio_data, samplerate
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None, None


def analyze_organic_samples(organic_dir: Path) -> Dict[str, Any]:
    """
    Analyze all organic samples in a directory.
    
    Args:
        organic_dir: Directory containing organic speech samples
        
    Returns:
        Dictionary of statistics
    """
    sensor = ProsodicContinuitySensor()
    
    # Collect metrics from all samples
    all_breaks_per_second = []
    all_total_breaks = []
    all_pitch_breaks = []
    all_energy_breaks = []
    all_centroid_breaks = []
    all_durations = []
    
    successful_analyses = 0
    failed_analyses = 0
    
    # Find all audio files
    audio_extensions = ['.wav', '.flac', '.mp3', '.ogg']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(organic_dir.glob(f'**/*{ext}'))
    
    logger.info(f"Found {len(audio_files)} audio files in {organic_dir}")
    
    for filepath in audio_files:
        logger.info(f"Analyzing: {filepath.name}")
        
        audio_data, samplerate = load_audio(filepath)
        if audio_data is None:
            failed_analyses += 1
            continue
        
        try:
            result = sensor.analyze(audio_data, samplerate)
            
            # Only collect statistics from valid analyses
            if result.passed is not None and result.metadata:
                all_breaks_per_second.append(result.metadata['breaks_per_second'])
                all_total_breaks.append(result.metadata['total_breaks'])
                all_pitch_breaks.append(result.metadata['pitch_breaks'])
                all_energy_breaks.append(result.metadata['energy_breaks'])
                all_centroid_breaks.append(result.metadata['centroid_breaks'])
                all_durations.append(result.metadata['total_speech_duration'])
                successful_analyses += 1
                
                logger.info(
                    f"  Breaks/sec: {result.metadata['breaks_per_second']:.2f}, "
                    f"Total: {result.metadata['total_breaks']}, "
                    f"Duration: {result.metadata['total_speech_duration']:.1f}s"
                )
            else:
                logger.warning(f"  Skipped (reason: {result.reason})")
                
        except Exception as e:
            logger.error(f"  Failed to analyze: {e}")
            failed_analyses += 1
    
    if successful_analyses == 0:
        logger.error("No samples could be analyzed successfully!")
        return None
    
    # Convert to numpy arrays for statistics
    breaks_per_second = np.array(all_breaks_per_second)
    total_breaks = np.array(all_total_breaks)
    pitch_breaks = np.array(all_pitch_breaks)
    energy_breaks = np.array(all_energy_breaks)
    centroid_breaks = np.array(all_centroid_breaks)
    durations = np.array(all_durations)
    
    # Compute statistics
    stats = {
        'num_samples': successful_analyses,
        'failed_samples': failed_analyses,
        'breaks_per_second': {
            'mean': float(np.mean(breaks_per_second)),
            'std': float(np.std(breaks_per_second)),
            'median': float(np.median(breaks_per_second)),
            'p50': float(np.percentile(breaks_per_second, 50)),
            'p90': float(np.percentile(breaks_per_second, 90)),
            'p95': float(np.percentile(breaks_per_second, 95)),
            'p99': float(np.percentile(breaks_per_second, 99)),
            'max': float(np.max(breaks_per_second)),
        },
        'total_breaks': {
            'mean': float(np.mean(total_breaks)),
            'std': float(np.std(total_breaks)),
            'median': float(np.median(total_breaks)),
        },
        'pitch_breaks': {
            'mean': float(np.mean(pitch_breaks)),
            'fraction_of_total': float(np.sum(pitch_breaks) / np.sum(total_breaks)),
        },
        'energy_breaks': {
            'mean': float(np.mean(energy_breaks)),
            'fraction_of_total': float(np.sum(energy_breaks) / np.sum(total_breaks)),
        },
        'centroid_breaks': {
            'mean': float(np.mean(centroid_breaks)),
            'fraction_of_total': float(np.sum(centroid_breaks) / np.sum(total_breaks)),
        },
        'speech_duration': {
            'mean': float(np.mean(durations)),
            'median': float(np.median(durations)),
        }
    }
    
    return stats


def recommend_thresholds(stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Recommend threshold values based on organic sample statistics.
    
    Strategy:
    - max_breaks_per_second: Use P95 or P99 of organic samples
    - risk_threshold: Set to catch outliers while allowing natural variation
    
    Args:
        stats: Statistics from organic samples
        
    Returns:
        Dictionary of recommended threshold values
    """
    # Use P95 + margin for max_breaks_per_second
    # This means 95% of organic samples are below this, with 5% headroom
    p95_breaks = stats['breaks_per_second']['p95']
    p99_breaks = stats['breaks_per_second']['p99']
    
    # Conservative: P99 with 20% margin
    recommended_max_breaks = p99_breaks * 1.2
    
    # Risk threshold: Use 0.7 as default (moderate sensitivity)
    # Can be adjusted based on FPR requirements
    recommended_risk_threshold = 0.7
    
    recommendations = {
        'max_breaks_per_second': round(recommended_max_breaks, 2),
        'risk_threshold': recommended_risk_threshold,
        'f0_zscore_threshold': 3.0,  # Standard outlier detection
        'energy_zscore_threshold': 3.0,
        'centroid_zscore_threshold': 3.0,
        'min_speech_duration': 0.5,
    }
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(
        description='Calibrate ProsodicContinuitySensor using organic speech samples'
    )
    parser.add_argument(
        '--organic-dir',
        type=Path,
        required=True,
        help='Directory containing organic speech samples'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output YAML config file with recommended settings'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output statistics in JSON format'
    )
    
    args = parser.parse_args()
    
    if not args.organic_dir.exists():
        logger.error(f"Directory not found: {args.organic_dir}")
        return 1
    
    logger.info("=" * 60)
    logger.info("ProsodicContinuitySensor Calibration")
    logger.info("=" * 60)
    logger.info(f"Organic samples directory: {args.organic_dir}")
    logger.info("")
    
    # Analyze samples
    stats = analyze_organic_samples(args.organic_dir)
    
    if stats is None:
        return 1
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("STATISTICS FROM ORGANIC SAMPLES")
    logger.info("=" * 60)
    logger.info(f"Samples analyzed: {stats['num_samples']}")
    logger.info(f"Failed samples: {stats['failed_samples']}")
    logger.info("")
    logger.info("Breaks per second:")
    logger.info(f"  Mean:   {stats['breaks_per_second']['mean']:.2f}")
    logger.info(f"  Median: {stats['breaks_per_second']['median']:.2f}")
    logger.info(f"  Std:    {stats['breaks_per_second']['std']:.2f}")
    logger.info(f"  P90:    {stats['breaks_per_second']['p90']:.2f}")
    logger.info(f"  P95:    {stats['breaks_per_second']['p95']:.2f}")
    logger.info(f"  P99:    {stats['breaks_per_second']['p99']:.2f}")
    logger.info(f"  Max:    {stats['breaks_per_second']['max']:.2f}")
    logger.info("")
    logger.info("Break types (fraction of total):")
    logger.info(f"  Pitch:    {stats['pitch_breaks']['fraction_of_total']:.1%}")
    logger.info(f"  Energy:   {stats['energy_breaks']['fraction_of_total']:.1%}")
    logger.info(f"  Centroid: {stats['centroid_breaks']['fraction_of_total']:.1%}")
    logger.info("")
    
    # Generate recommendations
    recommendations = recommend_thresholds(stats)
    
    logger.info("=" * 60)
    logger.info("RECOMMENDED THRESHOLDS")
    logger.info("=" * 60)
    for key, value in recommendations.items():
        logger.info(f"  {key}: {value}")
    logger.info("")
    
    # Output to file if requested
    if args.output:
        output_config = {
            'prosodic_continuity': recommendations,
            'calibration_metadata': {
                'num_samples': stats['num_samples'],
                'organic_breaks_p95': stats['breaks_per_second']['p95'],
                'organic_breaks_p99': stats['breaks_per_second']['p99'],
            }
        }
        
        with open(args.output, 'w') as f:
            yaml.dump(output_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved configuration to: {args.output}")
    
    if args.json:
        print(json.dumps({'statistics': stats, 'recommendations': recommendations}, indent=2))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
