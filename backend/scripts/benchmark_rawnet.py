#!/usr/bin/env python
"""
Benchmark RawNet3 Performance

Benchmarks RawNet3 model inference time and throughput.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import time
import statistics

import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from detection import DetectionPipeline
from detection.stages import RawNet3Stage
from detection.config import RawNet3Config
from detection.utils import convert_numpy_types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def benchmark_rawnet3(
    durations: list = None,
    sample_rate: int = 16000,
    n_iterations: int = 10,
    demo_mode: bool = True,
    output_dir: str = None,
) -> dict:
    """
    Benchmark RawNet3 inference performance.

    Args:
        durations: List of audio durations to test (seconds)
        sample_rate: Audio sample rate
        n_iterations: Number of iterations per duration
        demo_mode: Use demo mode
        output_dir: Output directory

    Returns:
        Benchmark results
    """
    if durations is None:
        durations = [1.0, 2.0, 5.0, 10.0, 30.0]

    config = RawNet3Config()
    stage = RawNet3Stage(config=config, demo_mode=demo_mode)

    results = {
        "sample_rate": sample_rate,
        "n_iterations": n_iterations,
        "demo_mode": demo_mode,
        "benchmarks": {},
    }

    for duration in durations:
        logger.info(f"Benchmarking {duration}s audio...")

        # Generate test audio
        n_samples = int(sample_rate * duration)
        audio = np.random.randn(n_samples).astype(np.float32)

        # Warm-up
        for _ in range(3):
            _ = stage.process(audio)

        # Benchmark
        times = []
        for i in range(n_iterations):
            start = time.perf_counter()
            _ = stage.process(audio)
            end = time.perf_counter()
            times.append(end - start)

        # Compute statistics
        mean_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)

        # Real-time factor (RTF)
        rtf = mean_time / duration

        results["benchmarks"][f"{duration}s"] = {
            "duration_seconds": duration,
            "n_samples": n_samples,
            "mean_time": mean_time,
            "std_time": std_time,
            "min_time": min_time,
            "max_time": max_time,
            "rtf": rtf,
            "throughput_samples_per_sec": n_samples / mean_time,
        }

        logger.info(
            f"  Duration: {duration}s | Mean time: {mean_time*1000:.2f}ms | RTF: {rtf:.4f}"
        )

    # Save results
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results_file = output_path / f"rawnet3_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(convert_numpy_types(results), f, indent=2)
        logger.info(f"Results saved to {results_file}")

    return results


def benchmark_pipeline(
    durations: list = None,
    sample_rate: int = 16000,
    n_iterations: int = 5,
    quick_mode: bool = False,
    output_dir: str = None,
) -> dict:
    """
    Benchmark full detection pipeline.

    Args:
        durations: List of audio durations to test
        sample_rate: Audio sample rate
        n_iterations: Number of iterations per duration
        quick_mode: Use quick mode (stages 1-3)
        output_dir: Output directory

    Returns:
        Benchmark results
    """
    if durations is None:
        durations = [1.0, 2.0, 5.0, 10.0]

    pipeline = DetectionPipeline()

    results = {
        "sample_rate": sample_rate,
        "n_iterations": n_iterations,
        "quick_mode": quick_mode,
        "benchmarks": {},
    }

    for duration in durations:
        logger.info(f"Benchmarking pipeline on {duration}s audio (quick_mode={quick_mode})...")

        # Generate test audio
        n_samples = int(sample_rate * duration)
        audio = np.random.randn(n_samples).astype(np.float32)

        # Warm-up
        for _ in range(2):
            _ = pipeline.detect(audio, quick_mode=quick_mode)

        # Benchmark
        times = []
        for i in range(n_iterations):
            start = time.perf_counter()
            _ = pipeline.detect(audio, quick_mode=quick_mode)
            end = time.perf_counter()
            times.append(end - start)

        # Compute statistics
        mean_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)
        rtf = mean_time / duration

        results["benchmarks"][f"{duration}s"] = {
            "duration_seconds": duration,
            "n_samples": n_samples,
            "mean_time": mean_time,
            "std_time": std_time,
            "min_time": min_time,
            "max_time": max_time,
            "rtf": rtf,
        }

        logger.info(
            f"  Duration: {duration}s | Mean time: {mean_time*1000:.2f}ms | RTF: {rtf:.4f}"
        )

    # Save results
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        mode_suffix = "quick" if quick_mode else "full"
        results_file = output_path / f"pipeline_benchmark_{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(convert_numpy_types(results), f, indent=2)
        logger.info(f"Results saved to {results_file}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark RawNet3 Performance")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark_results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--n-iterations",
        type=int,
        default=10,
        help="Number of iterations per test",
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        default=True,
        help="Use demo mode",
    )
    parser.add_argument(
        "--benchmark-pipeline",
        action="store_true",
        help="Benchmark full pipeline instead of just RawNet3",
    )
    parser.add_argument(
        "--quick-mode",
        action="store_true",
        help="Use quick mode for pipeline benchmark",
    )

    args = parser.parse_args()

    logger.info("Starting benchmark")

    if args.benchmark_pipeline:
        # Benchmark full pipeline
        results = benchmark_pipeline(
            n_iterations=args.n_iterations,
            quick_mode=args.quick_mode,
            output_dir=args.output_dir,
        )

        print("\n" + "=" * 70)
        print("PIPELINE BENCHMARK RESULTS")
        print("=" * 70)
        print(f"Mode: {'Quick (stages 1-3)' if args.quick_mode else 'Full (all stages)'}")
        print(f"Iterations per test: {args.n_iterations}")
        print("-" * 70)
        print(f"{'Duration':>10} | {'Mean Time':>12} | {'Std Dev':>12} | {'RTF':>10}")
        print("-" * 70)

        for key, data in results["benchmarks"].items():
            print(
                f"{key:>10} | {data['mean_time']*1000:>10.2f}ms | "
                f"{data['std_time']*1000:>10.2f}ms | {data['rtf']:>10.4f}"
            )

    else:
        # Benchmark RawNet3
        results = benchmark_rawnet3(
            n_iterations=args.n_iterations,
            demo_mode=args.demo_mode,
            output_dir=args.output_dir,
        )

        print("\n" + "=" * 70)
        print("RAWNET3 BENCHMARK RESULTS")
        print("=" * 70)
        print(f"Demo mode: {args.demo_mode}")
        print(f"Iterations per test: {args.n_iterations}")
        print("-" * 70)
        print(f"{'Duration':>10} | {'Mean Time':>12} | {'Throughput':>15} | {'RTF':>10}")
        print("-" * 70)

        for key, data in results["benchmarks"].items():
            throughput = data["throughput_samples_per_sec"] / 1000
            print(
                f"{key:>10} | {data['mean_time']*1000:>10.2f}ms | "
                f"{throughput:>12.1f}K/s | {data['rtf']:>10.4f}"
            )

    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
