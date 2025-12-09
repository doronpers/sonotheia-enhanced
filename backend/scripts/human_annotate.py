#!/usr/bin/env python3
"""
Human Annotation Tool for Deepfake Detection Calibration

This tool allows a human listener to:
1. Listen to audio samples
2. Review algorithm detection results
3. Provide ground truth labels and artifact annotations
4. Build a calibration dataset for threshold optimization

Usage:
    python human_annotate.py --audio-dir data/samples --output annotations.jsonl
    python human_annotate.py --audio-file sample.wav --interactive
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("human_annotate")

# Artifact taxonomy for consistent labeling
ARTIFACT_TYPES = {
    "two_mouth": {
        "description": "Overlapping/conflicting articulations (sounds like two voices)",
        "sensor": "TwoMouthSensor",
        "examples": ["voice morphing", "glitchy overlap", "speaker size changes"]
    },
    "hard_attack": {
        "description": "Unnatural word onset - too fast, no breath turbulence",
        "sensor": "GlottalInertiaSensor",
        "examples": ["words pop in from silence", "no plosive burst", "too clean start"]
    },
    "hard_decay": {
        "description": "Unnatural word ending - abrupt cutoff, no room reverb",
        "sensor": "GlottalInertiaSensor",
        "examples": ["word just stops", "no tail/decay", "digital silence after"]
    },
    "infinite_lung": {
        "description": "Speech continues too long without breath",
        "sensor": "BreathSensor",
        "examples": ["no breathing pauses", ">15s continuous speech"]
    },
    "robotic_transitions": {
        "description": "Choppy or mechanical phoneme transitions",
        "sensor": "CoarticulationSensor",
        "examples": ["syllables don't blend", "concatenated feel"]
    },
    "metallic_phase": {
        "description": "Hollow/metallic quality from phase artifacts",
        "sensor": "PhaseCoherenceSensor",
        "examples": ["vocoder sound", "hollow vowels", "digital shimmer"]
    },
    "spliced_silence": {
        "description": "Digital silence (perfect zero) between words",
        "sensor": "DigitalSilenceSensor",
        "examples": ["too-perfect silence", "no ambient noise", "digital black"]
    },
    "formant_jump": {
        "description": "Unnatural pitch/formant discontinuities",
        "sensor": "FormantTrajectorySensor",
        "examples": ["pitch jumps", "voice breaks unnaturally", "frequency glitches"]
    },
    "other": {
        "description": "Other artifact not listed above",
        "sensor": "unknown",
        "examples": []
    }
}


@dataclass
class HumanAnnotation:
    """Human annotation for a single audio sample."""
    audio_file: str
    timestamp: str

    # Human verdict
    human_verdict: str  # REAL, SYNTHETIC, UNSURE
    confidence: str     # HIGH, MEDIUM, LOW

    # Artifact annotations
    artifacts_heard: List[str]  # List of artifact type keys
    artifact_timestamps: Dict[str, str]  # artifact_type -> "start-end" or "throughout"

    # Algorithm comparison
    algorithm_verdict: Optional[str] = None
    algorithm_score: Optional[float] = None
    sensor_results: Optional[Dict[str, Any]] = None

    # Human vs Algorithm agreement
    agrees_with_algorithm: Optional[bool] = None
    disagreement_notes: Optional[str] = None

    # Free-form notes
    notes: str = ""


def run_detection(audio_path: str) -> Dict[str, Any]:
    """Run the detection pipeline on an audio file."""
    try:
        import numpy as np
        import soundfile as sf
        from sensors.registry import get_default_sensors, SensorRegistry
        from sensors.fusion import calculate_fusion_verdict

        # Load audio
        audio, sr = sf.read(audio_path)
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)  # Mono
        audio = audio.astype(np.float32)

        # Run sensors
        registry = SensorRegistry()
        for sensor in get_default_sensors():
            try:
                registry.register(sensor)
            except Exception:
                pass  # Some sensors may fail to init

        # Note: This is sync version for simplicity
        results = {}
        for name in registry.list_sensors():
            sensor = registry.get_sensor(name)
            if sensor:
                try:
                    result = sensor.analyze(audio, sr)
                    results[name] = {
                        "passed": result.passed,
                        "value": result.value,
                        "threshold": result.threshold,
                        "detail": result.detail,
                        "metadata": result.metadata
                    }
                except Exception as e:
                    results[name] = {"error": str(e)}

        # Calculate fusion verdict
        from sensors.base import SensorResult
        sensor_results = []
        for name, r in results.items():
            if "error" not in r:
                sensor_results.append(SensorResult(
                    sensor_name=name,
                    passed=r["passed"],
                    value=r["value"],
                    threshold=r["threshold"],
                    detail=r.get("detail"),
                    metadata=r.get("metadata", {})
                ))

        fusion = calculate_fusion_verdict(sensor_results)

        return {
            "verdict": fusion.get("verdict", "UNKNOWN"),
            "score": fusion.get("global_risk_score", 0.5),
            "sensors": results
        }

    except Exception as e:
        logger.error(f"Detection failed: {e}")
        return {"verdict": "ERROR", "score": 0.0, "sensors": {}, "error": str(e)}


def print_artifact_menu():
    """Print the artifact type menu for selection."""
    print("\n" + "=" * 60)
    print("ARTIFACT TYPES (enter numbers separated by commas, or 'none')")
    print("=" * 60)
    for i, (key, info) in enumerate(ARTIFACT_TYPES.items(), 1):
        print(f"  {i}. [{key}]")
        print(f"     {info['description']}")
        print(f"     Sensor: {info['sensor']}")
        if info['examples']:
            print(f"     Examples: {', '.join(info['examples'])}")
        print()


def interactive_annotate(audio_path: str, detection_result: Dict) -> HumanAnnotation:
    """Interactive annotation session for a single audio file."""
    print("\n" + "=" * 70)
    print(f"ANNOTATING: {audio_path}")
    print("=" * 70)

    # Show algorithm results
    print("\n--- ALGORITHM RESULTS ---")
    print(f"Verdict: {detection_result['verdict']}")
    print(f"Risk Score: {detection_result['score']:.3f}")
    print("\nSensor Results:")
    for name, result in detection_result.get('sensors', {}).items():
        if 'error' in result:
            print(f"  {name}: ERROR - {result['error']}")
        else:
            status = "PASS" if result['passed'] else "FAIL" if result['passed'] is False else "INFO"
            print(f"  {name}: {status} (value={result['value']:.3f}, threshold={result['threshold']:.3f})")

    # Prompt for playback
    print("\n--- LISTEN TO AUDIO ---")
    print(f"File: {audio_path}")
    print("(Use your system audio player to listen, or press Enter to continue)")

    # Try to play audio if possible
    try:
        import subprocess
        # Try common players
        for player in ['afplay', 'aplay', 'play', 'mpv', 'ffplay']:
            try:
                subprocess.run([player, audio_path], capture_output=True, timeout=60)
                break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    except Exception:
        pass

    input("\nPress Enter after listening...")

    # Get human verdict
    print("\n--- YOUR VERDICT ---")
    while True:
        verdict = input("Is this audio REAL, SYNTHETIC, or UNSURE? [R/S/U]: ").strip().upper()
        if verdict in ['R', 'REAL']:
            human_verdict = "REAL"
            break
        elif verdict in ['S', 'SYNTHETIC']:
            human_verdict = "SYNTHETIC"
            break
        elif verdict in ['U', 'UNSURE']:
            human_verdict = "UNSURE"
            break
        print("Please enter R, S, or U")

    # Get confidence
    while True:
        conf = input("Confidence level? [H]igh, [M]edium, [L]ow: ").strip().upper()
        if conf in ['H', 'HIGH']:
            confidence = "HIGH"
            break
        elif conf in ['M', 'MEDIUM']:
            confidence = "MEDIUM"
            break
        elif conf in ['L', 'LOW']:
            confidence = "LOW"
            break
        print("Please enter H, M, or L")

    # Get artifacts
    print_artifact_menu()
    artifacts_input = input("Enter artifact numbers (comma-separated) or 'none': ").strip()

    artifacts_heard = []
    if artifacts_input.lower() != 'none' and artifacts_input:
        artifact_keys = list(ARTIFACT_TYPES.keys())
        for num in artifacts_input.split(','):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(artifact_keys):
                    artifacts_heard.append(artifact_keys[idx])
            except ValueError:
                pass

    # Get timestamps for artifacts
    artifact_timestamps = {}
    for artifact in artifacts_heard:
        ts = input(f"  When did you hear '{artifact}'? (e.g., '0:02-0:05' or 'throughout'): ").strip()
        artifact_timestamps[artifact] = ts or "unspecified"

    # Agreement check
    algo_verdict = detection_result['verdict']
    if algo_verdict in ['REAL', 'SYNTHETIC']:
        agrees = (human_verdict == algo_verdict)
    else:
        agrees = None

    disagreement_notes = None
    if agrees is False:
        disagreement_notes = input("\nYou disagree with the algorithm. Why? (brief note): ").strip()

    # Additional notes
    notes = input("\nAny additional notes? (or press Enter to skip): ").strip()

    return HumanAnnotation(
        audio_file=str(audio_path),
        timestamp=datetime.now().isoformat(),
        human_verdict=human_verdict,
        confidence=confidence,
        artifacts_heard=artifacts_heard,
        artifact_timestamps=artifact_timestamps,
        algorithm_verdict=algo_verdict,
        algorithm_score=detection_result['score'],
        sensor_results=detection_result.get('sensors'),
        agrees_with_algorithm=agrees,
        disagreement_notes=disagreement_notes,
        notes=notes
    )


def save_annotation(annotation: HumanAnnotation, output_file: str):
    """Append annotation to JSONL file."""
    with open(output_file, 'a') as f:
        f.write(json.dumps(asdict(annotation)) + '\n')
    logger.info(f"Saved annotation to {output_file}")


def organize_calibration_dataset(annotation: HumanAnnotation, dataset_dir: str):
    """Copy audio file to calibration dataset organized by verdict."""
    import shutil

    dataset_path = Path(dataset_dir)
    verdict_dir = dataset_path / annotation.human_verdict.lower()
    verdict_dir.mkdir(parents=True, exist_ok=True)

    src = Path(annotation.audio_file)
    dst = verdict_dir / src.name

    if not dst.exists():
        shutil.copy2(src, dst)
        logger.info(f"Copied to calibration dataset: {dst}")


def main():
    parser = argparse.ArgumentParser(
        description="Human annotation tool for deepfake detection calibration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Artifact Types:
  two_mouth      - Overlapping articulations (two voices)
  hard_attack    - Unnatural word onset
  hard_decay     - Abrupt word ending
  infinite_lung  - No breathing pauses
  robotic_trans  - Choppy phoneme transitions
  metallic_phase - Hollow/vocoder quality
  spliced_silence - Digital silence
  formant_jump   - Pitch discontinuities

Examples:
  # Annotate a single file
  python human_annotate.py --audio-file sample.wav --interactive

  # Batch annotate a directory
  python human_annotate.py --audio-dir data/samples --output annotations.jsonl

  # Build calibration dataset from annotations
  python human_annotate.py --audio-dir data/samples --calibration-dir data/calibration
        """
    )
    parser.add_argument('--audio-file', type=str, help='Single audio file to annotate')
    parser.add_argument('--audio-dir', type=str, help='Directory of audio files to annotate')
    parser.add_argument('--output', type=str, default='human_annotations.jsonl',
                        help='Output JSONL file for annotations')
    parser.add_argument('--calibration-dir', type=str, default='backend/data/calibration',
                        help='Directory to organize calibration dataset')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--skip-detection', action='store_true',
                        help='Skip running detection (faster, no comparison)')
    parser.add_argument('--list-artifacts', action='store_true', help='Print artifact taxonomy and exit')

    args = parser.parse_args()

    if args.list_artifacts:
        print_artifact_menu()
        return

    # Collect audio files
    audio_files = []
    if args.audio_file:
        audio_files = [args.audio_file]
    elif args.audio_dir:
        audio_dir = Path(args.audio_dir)
        audio_files = list(audio_dir.glob('*.wav')) + list(audio_dir.glob('*.mp3')) + \
                      list(audio_dir.glob('*.flac')) + list(audio_dir.glob('*.m4a'))

    if not audio_files:
        print("No audio files found. Use --audio-file or --audio-dir")
        return

    print(f"\nFound {len(audio_files)} audio files to annotate")
    print(f"Annotations will be saved to: {args.output}")
    print(f"Calibration dataset: {args.calibration_dir}")

    # Process each file
    for i, audio_path in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {audio_path}")

        # Run detection
        if args.skip_detection:
            detection_result = {"verdict": "SKIPPED", "score": 0.0, "sensors": {}}
        else:
            print("  Running detection...")
            detection_result = run_detection(str(audio_path))

        # Interactive annotation
        if args.interactive or len(audio_files) == 1:
            annotation = interactive_annotate(str(audio_path), detection_result)
        else:
            # Non-interactive: just record detection result with placeholder
            annotation = HumanAnnotation(
                audio_file=str(audio_path),
                timestamp=datetime.now().isoformat(),
                human_verdict="PENDING",
                confidence="PENDING",
                artifacts_heard=[],
                artifact_timestamps={},
                algorithm_verdict=detection_result['verdict'],
                algorithm_score=detection_result['score'],
                sensor_results=detection_result.get('sensors'),
            )

        # Save annotation
        save_annotation(annotation, args.output)

        # Organize into calibration dataset
        if annotation.human_verdict not in ["PENDING", "UNSURE"]:
            organize_calibration_dataset(annotation, args.calibration_dir)

    print(f"\n{'=' * 60}")
    print("ANNOTATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Annotations saved to: {args.output}")
    print(f"Calibration dataset: {args.calibration_dir}")
    print(f"\nNext steps:")
    print(f"  1. Review annotations: cat {args.output} | jq .")
    print(f"  2. Run threshold optimizer: python calibration/optimizer.py --dataset {args.calibration_dir}")
    print(f"  3. Evaluate new thresholds: python scripts/eval_liveness.py --dataset-dir {args.calibration_dir}")


if __name__ == "__main__":
    main()
