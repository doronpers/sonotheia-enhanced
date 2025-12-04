import sys
import os
import numpy as np

# Add backend and root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sensors.registry import SensorRegistry, get_default_sensors
from sensors.glottal_inertia import GlottalInertiaSensor
from sensors.digital_silence import DigitalSilenceSensor
from sensors.phase_coherence import PhaseCoherenceSensor
from sensors.global_formants import GlobalFormantSensor

def test_sensor_registration():
    print("Testing sensor registration...")
    registry = SensorRegistry()
    
    # Register default sensors
    defaults = get_default_sensors()
    for sensor in defaults:
        registry.register(sensor)
        
    # Check if new sensors are registered
    sensors = registry.list_sensors()
    print(f"Registered sensors: {sensors}")
    
    has_glottal = any(isinstance(s, GlottalInertiaSensor) for s in defaults)
    has_silence = any(isinstance(s, DigitalSilenceSensor) for s in defaults)
    
    if has_glottal and has_silence:
        print("PASS: New sensors are in default sensors list.")
    else:
        print("FAIL: New sensors NOT in default sensors list.")
        return False
        
    return True

def test_glottal_inertia():
    print("\nTesting GlottalInertiaSensor...")
    sensor = GlottalInertiaSensor()
    
    # Create dummy audio (silence + instantaneous burst)
    sr = 16000
    duration = 1.0
    audio = np.zeros(int(sr * duration))
    # Add a burst at 0.5s with instant rise
    start_idx = int(0.5 * sr)
    audio[start_idx:] = 0.5 
    
    # Run analysis
    result = sensor.analyze(audio, sr)
    print(f"Result detail: {result.detail}")
    
    # Should detect violation
    if not result.passed:
        print("PASS: GlottalInertiaSensor correctly flagged instant rise.")
    else:
        print("FAIL: GlottalInertiaSensor failed to flag instant rise.")
        return False
    return True

def test_digital_silence():
    print("\nTesting DigitalSilenceSensor...")
    sensor = DigitalSilenceSensor()
    
    # Create dummy audio (perfect silence)
    sr = 16000
    duration = 1.0
    audio = np.zeros(int(sr * duration))
    
    # Run analysis
    result = sensor.analyze(audio, sr)
    print(f"Result detail: {result.detail}")
    
    # Should detect violation
    if not result.passed:
        print("PASS: DigitalSilenceSensor correctly flagged perfect silence.")
    else:
        print("FAIL: DigitalSilenceSensor failed to flag perfect silence.")
        return False
    return True

def test_phase_coherence_entropy():
    print("\nTesting PhaseCoherenceSensor (Entropy)...")
    sensor = PhaseCoherenceSensor()
    
    # Create dummy audio (white noise -> high entropy)
    sr = 16000
    duration = 1.0
    audio = np.random.normal(0, 0.1, int(sr * duration))
    
    # Run analysis
    result = sensor.analyze(audio, sr)
    print(f"Result detail: {result.detail}")
    print(f"Metadata: {result.metadata}")
    
    # White noise should have high entropy, so it might pass or fail depending on threshold
    # But we just want to ensure it runs and computes entropy
    if "phase_entropy" in result.metadata:
        print(f"PASS: PhaseCoherenceSensor computed entropy: {result.metadata['phase_entropy']}")
    else:
        print("FAIL: PhaseCoherenceSensor did not compute entropy.")
        return False
    return True

def test_global_formants():
    print("\nTesting GlobalFormantSensor...")
    sensor = GlobalFormantSensor()
    
    # Create dummy audio (white noise -> flat spectrum)
    sr = 16000
    duration = 1.0
    audio = np.random.normal(0, 0.1, int(sr * duration))
    
    # Run analysis
    result = sensor.analyze(audio, sr)
    print(f"Result detail: {result.detail}")
    print(f"Metadata: {result.metadata}")
    
    # White noise should have high flatness
    if result.metadata.get("flatness", 0) > 0.4:
        print(f"PASS: GlobalFormantSensor detected high flatness: {result.metadata['flatness']}")
    else:
        print(f"FAIL: GlobalFormantSensor failed to detect high flatness (got {result.metadata.get('flatness')})")
        return False
    return True

def test_formant_trajectory():
    print("\nTesting FormantTrajectorySensor (Cepstral)...")
    from sensors.formant import FormantTrajectorySensor
    sensor = FormantTrajectorySensor()
    
    # Create dummy audio (stable harmonics to simulate formants)
    sr = 16000
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration))
    # Mix of 500Hz, 1500Hz, 2500Hz
    audio = (0.5 * np.sin(2 * np.pi * 500 * t) + 
             0.3 * np.sin(2 * np.pi * 1500 * t) + 
             0.2 * np.sin(2 * np.pi * 2500 * t))
    
    # Run analysis
    result = sensor.analyze(audio, sr)
    print(f"Result detail: {result.detail}")
    print(f"Metadata keys: {result.metadata.keys()}")
    
    # Should pass as trajectory is perfectly stable
    if result.passed:
        print("PASS: FormantTrajectorySensor passed stable signal.")
    else:
        print(f"FAIL: FormantTrajectorySensor failed stable signal. Value: {result.value}")
        return False
    return True

if __name__ == "__main__":
    success = True
    success &= test_sensor_registration()
    success &= test_glottal_inertia()
    success &= test_digital_silence()
    success &= test_phase_coherence_entropy()
    success &= test_global_formants()
    success &= test_formant_trajectory()
    
    if success:
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
