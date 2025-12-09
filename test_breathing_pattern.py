#!/usr/bin/env python3
"""
Test script for Breathing Pattern Analysis Sensor

This script demonstrates the breathing pattern sensor for deepfake detection.
It analyzes audio files for breathing regularity using spectral analysis.

Usage:
    python test_breathing_pattern.py <audio_file_path>

Example:
    python test_breathing_pattern.py samples/authentic_speech.wav
    python test_breathing_pattern.py samples/synthetic_speech.wav

The sensor returns:
- High regularity score (close to 1.0): Irregular breathing (likely authentic)
- Low regularity score (close to 0.0): Regular breathing (likely synthetic)
"""

import sys
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

# Add backend to path if running from project root
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import base sensor first
import importlib.util

def import_module_from_file(module_name, file_path):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import base sensor module
base_module = import_module_from_file(
    "sensors.base",
    backend_path / "sensors" / "base.py"
)

# Import utils.config for breathing_pattern sensor
config_module = import_module_from_file(
    "utils.config",
    backend_path / "utils" / "config.py"
)

# Import breathing pattern sensor
breathing_pattern = import_module_from_file(
    "sensors.breathing_pattern",
    backend_path / "sensors" / "breathing_pattern.py"
)

BreathingPatternSensor = breathing_pattern.BreathingPatternSensor


def load_audio(audio_path: str, target_sr: int = 16000):
    """Load audio file using librosa."""
    audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    return audio, sr


def save_audio(audio: np.ndarray, file_path: str, sr: int = 16000):
    """Save audio to file."""
    sf.write(file_path, audio, sr)


def analyze_audio_file(audio_path: str):
    """
    Analyze an audio file for breathing pattern regularity.

    Args:
        audio_path: Path to audio file
    """
    print(f"\n{'='*70}")
    print(f"Breathing Pattern Analysis: {Path(audio_path).name}")
    print(f"{'='*70}\n")

    # Check if file exists
    if not Path(audio_path).exists():
        print(f"❌ Error: File not found: {audio_path}")
        return

    try:
        # Load audio
        print("📂 Loading audio file...")
        audio_data, sample_rate = load_audio(audio_path, target_sr=16000)
        duration = len(audio_data) / sample_rate
        print(f"   ✓ Loaded: {duration:.2f}s @ {sample_rate}Hz")

        # Create sensor
        sensor = BreathingPatternSensor()

        # Analyze
        print("\n🔍 Analyzing breathing patterns...")
        result = sensor.analyze(audio_data, sample_rate)

        # Display results
        print(f"\n{'─'*70}")
        print("RESULTS")
        print(f"{'─'*70}\n")

        print(f"Sensor: {result.sensor_name}")
        print(f"Regularity Score: {result.value:.3f}")
        print(f"Passed: {result.passed}")

        if result.metadata:
            print("\nMetadata:")
            for key, value in result.metadata.items():
                if isinstance(value, float):
                    print(f"  - {key}: {value:.3f}")
                else:
                    print(f"  - {key}: {value}")

        print(f"\nDetail: {result.detail}")

        if result.reason:
            print(f"Reason: {result.reason}")

        # Interpretation
        print(f"\n{'─'*70}")
        print("INTERPRETATION")
        print(f"{'─'*70}\n")

        if result.metadata and result.metadata.get("rejected"):
            print("⚠️  Analysis rejected due to high background noise.")
            print("    SNR is too low for reliable breath detection.")
        elif result.value >= 0.7:
            print("✅ High breathing irregularity detected (LIKELY AUTHENTIC)")
            print("   Real human breathing shows natural temporal variability.")
        elif result.value >= 0.5:
            print("⚠️  Moderate breathing regularity (BORDERLINE)")
            print("   Additional analysis recommended.")
        else:
            print("🚨 High breathing regularity detected (LIKELY SYNTHETIC)")
            print("   Unnaturally consistent breathing pattern suggests AI-generated audio.")

        print(f"\n{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Error analyzing audio: {e}")
        import traceback
        traceback.print_exc()


def create_test_audio():
    """
    Create synthetic test audio samples for demonstration.
    """
    print("\n📝 Creating test audio samples...")

    # Create samples directory if it doesn't exist
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)

    # Sample 1: Synthetic speech with regular breathing
    # (simplified simulation - actual synthetic audio would be more complex)
    sr = 16000
    duration = 10.0  # 10 seconds
    t = np.linspace(0, duration, int(sr * duration))

    # Regular breathing pattern (breaths every 2 seconds exactly)
    regular_breath = np.zeros_like(t)
    for breath_time in np.arange(0, duration, 2.0):  # Every 2 seconds exactly
        breath_idx = int(breath_time * sr)
        breath_duration = int(0.3 * sr)  # 300ms breath
        if breath_idx + breath_duration < len(t):
            # Add breath sound (low frequency noise)
            breath_signal = np.random.randn(breath_duration) * 0.1
            # Filter to 20-300Hz range
            from scipy import signal
            sos = signal.butter(4, [20, 300], 'bandpass', fs=sr, output='sos')
            breath_signal = signal.sosfilt(sos, breath_signal)
            regular_breath[breath_idx:breath_idx+breath_duration] = breath_signal

    # Add some speech-like content (simplified)
    speech = np.sin(2 * np.pi * 500 * t) * 0.3 * (np.sin(2 * np.pi * 0.5 * t) > 0)
    regular_audio = regular_breath + speech

    # Sample 2: Authentic-like speech with irregular breathing
    irregular_breath = np.zeros_like(t)
    # Irregular intervals: vary between 1.5 and 3.5 seconds
    breath_times = []
    current_time = 0.0
    while current_time < duration:
        interval = np.random.uniform(1.5, 3.5)  # Variable intervals
        current_time += interval
        breath_times.append(current_time)

    for breath_time in breath_times:
        if breath_time >= duration:
            break
        breath_idx = int(breath_time * sr)
        breath_duration = int(np.random.uniform(0.2, 0.4) * sr)  # Variable duration
        if breath_idx + breath_duration < len(t):
            breath_signal = np.random.randn(breath_duration) * 0.1
            from scipy import signal
            sos = signal.butter(4, [20, 300], 'bandpass', fs=sr, output='sos')
            breath_signal = signal.sosfilt(sos, breath_signal)
            irregular_breath[breath_idx:breath_idx+breath_duration] = breath_signal

    irregular_audio = irregular_breath + speech

    # Normalize
    regular_audio = regular_audio / np.max(np.abs(regular_audio)) * 0.9
    irregular_audio = irregular_audio / np.max(np.abs(irregular_audio)) * 0.9

    # Save samples
    regular_path = samples_dir / "synthetic_regular_breathing.wav"
    irregular_path = samples_dir / "authentic_irregular_breathing.wav"

    save_audio(regular_audio, str(regular_path), sr)
    save_audio(irregular_audio, str(irregular_path), sr)

    print(f"   ✓ Created: {regular_path}")
    print(f"   ✓ Created: {irregular_path}")

    return str(regular_path), str(irregular_path)


def main():
    """Main entry point for the test script."""
    print("\n" + "="*70)
    print(" "*15 + "BREATHING PATTERN ANALYSIS DEMO")
    print("="*70)

    # Check if audio file path is provided
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        analyze_audio_file(audio_path)
    else:
        print("\nNo audio file provided. Creating test samples...\n")

        # Create test samples
        regular_path, irregular_path = create_test_audio()

        # Analyze both samples
        print("\n" + "="*70)
        print("ANALYZING SYNTHETIC AUDIO (Regular Breathing)")
        print("="*70)
        analyze_audio_file(regular_path)

        print("\n" + "="*70)
        print("ANALYZING AUTHENTIC-LIKE AUDIO (Irregular Breathing)")
        print("="*70)
        analyze_audio_file(irregular_path)

        print("\n💡 TIP: You can also analyze your own audio files:")
        print(f"    python {sys.argv[0]} <path_to_audio_file>\n")


if __name__ == "__main__":
    main()
