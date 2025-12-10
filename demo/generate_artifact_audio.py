import numpy as np
import scipy.io.wavfile as wav
import json
import os

SAMPLE_RATE = 44100
DURATION = 5.0  # seconds
OUTPUT_WAV = os.path.join(os.path.dirname(__file__), "artifact_sample.wav")
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "artifact_metadata.json")

def generate_sine_wave(freq, duration, sample_rate=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)

def generate_noise(duration, sample_rate=SAMPLE_RATE):
    return np.random.normal(0, 0.5, int(sample_rate * duration))

def generate_audio():
    print("Generating authentic artifact audio...")
    
    # 1. Base Signal (Simulated Voice-like Harmonic Stack)
    t_full = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    # Fundamental frequency f0 varying slightly (intonation)
    f0 = 120 + 10 * np.sin(2 * np.pi * 0.5 * t_full) 
    
    signal = np.zeros_like(t_full)
    # Add harmonics (Formants approximation)
    for i in range(1, 10):
        signal += (1.0 / i) * np.sin(2 * np.pi * i * f0 * t_full)
    
    # Envelope to make it sound like speech bursts
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t_full) # 2 syllables per second
    signal *= envelope
    
    # Add some background noise
    signal += np.random.normal(0, 0.02, len(signal))

    # --- INJECT ARTIFACTS ---
    metadata = []

    # Artifact A: "Vocoder Grid" (High Frequency Robotic Buzz)
    # Time: 1.5s to 2.5s
    # Freq: 4000Hz - 8000Hz (simulated by adding high freq tones)
    start_A, end_A = 1.5, 2.5
    idx_start_A = int(start_A * SAMPLE_RATE)
    idx_end_A = int(end_A * SAMPLE_RATE)
    
    # Generate metallic buzzing
    t_art_A = t_full[idx_start_A:idx_end_A]
    artifact_A = 0.3 * np.sin(2 * np.pi * 6000 * t_art_A) * np.sin(2 * np.pi * 50 * t_art_A) # Modulated
    signal[idx_start_A:idx_end_A] += artifact_A
    
    metadata.append({
        "id": "ART-001",
        "name": "Vocoder Artifact",
        "description": "High-frequency metallic buzzing indicative of neural vocoders.",
        "startTime": start_A,
        "endTime": end_A,
        "freqMin": 4000,
        "freqMax": 8000,
        "color": "#ef4444" # Red
    })

    # Artifact B: "Phase Discontinuity" (Abrupt Cut / Silence / Click)
    # Time: 3.5s to 3.55s (Very short)
    # Freq: Broadband
    start_B, end_B = 3.5, 3.55
    idx_start_B = int(start_B * SAMPLE_RATE)
    idx_end_B = int(end_B * SAMPLE_RATE)
    
    # Zero out signal (hard cut) then impulse
    signal[idx_start_B:idx_end_B] = 0.0 
    signal[idx_end_B-100:idx_end_B] = 1.0 # Click at end
    
    metadata.append({
        "id": "ART-002",
        "name": "Phase Discontinuity",
        "description": "Unnatural signal cutoff not present in biological speech.",
        "startTime": start_B,
        "endTime": end_B,
        "freqMin": 0,
        "freqMax": 20000, # Broadband click
        "color": "#f59e0b" # Orange
    })

    # Normalize
    signal = signal / np.max(np.abs(signal))
    
    # Save Wave file
    wav.write(OUTPUT_WAV, SAMPLE_RATE, (signal * 32767).astype(np.int16))
    print(f"Audio saved to: {OUTPUT_WAV}")

    # Save Metadata
    with open(OUTPUT_JSON, "w") as f:
        json.dump({
            "duration": DURATION,
            "sampleRate": SAMPLE_RATE,
            "filename": "artifact_sample.wav",
            "artifacts": metadata
        }, f, indent=2)
    print(f"Metadata saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    generate_audio()
