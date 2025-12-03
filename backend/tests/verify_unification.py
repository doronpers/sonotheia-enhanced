import asyncio
import numpy as np
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import sys
from unittest.mock import MagicMock

# Mock librosa
librosa_mock = MagicMock()
librosa_mock.feature.melspectrogram.return_value = np.zeros((128, 100))
librosa_mock.power_to_db.return_value = np.zeros((128, 100))
librosa_mock.feature.delta.return_value = np.zeros((128, 100))
librosa_mock.effects.preemphasis.return_value = np.zeros(100)
librosa_mock.util.frame.return_value = np.zeros((100, 10))
librosa_mock.lpc.return_value = np.zeros(10)
sys.modules["librosa"] = librosa_mock

from backend.sensors.base import BaseSensor, SensorResult
from backend.sensors.registry import SensorRegistry
from backend.sensors.phase_coherence import PhaseCoherenceSensor
from backend.sensors.vocal_tract import VocalTractSensor
from backend.sensors.coarticulation import CoarticulationSensor
from backend.sensors.huggingface_detector import HuggingFaceDetectorSensor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

async def verify_sensors():
    logger.info("Starting verification...")
    
    # 1. Create dummy audio
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration))
    # Mix of sine waves and noise
    audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
    audio = audio.astype(np.float32)
    
    # 2. Initialize Registry
    registry = SensorRegistry()
    
    # 3. Register Sensors
    registry.register(PhaseCoherenceSensor)
    registry.register(VocalTractSensor)
    registry.register(CoarticulationSensor)
    registry.register(HuggingFaceDetectorSensor)
    
    logger.info("Sensors registered.")
    
    # 4. Run Analysis
    logger.info("Running analysis...")
    results = await registry.analyze_all(audio, sr)
    
    # 5. Check Results
    for name, result in results.items():
        logger.info(f"Sensor: {name}")
        logger.info(f"  Passed: {result['passed']}")
        logger.info(f"  Value: {result['value']}")
        logger.info(f"  Detail: {result['detail']}")
        
        if result['passed'] is None and name != "HuggingFace Detector":
             logger.error(f"Sensor {name} returned None for passed status (unexpected for physics sensors)")

    # 6. Verify Timeout Logic
    logger.info("Verifying timeout logic...")
    class SlowSensor(BaseSensor):
        def analyze(self, audio_data, samplerate):
            import time
            time.sleep(2.0) # Sleep longer than timeout
            return SensorResult("Slow", True, 1.0, 0.5, None, None)
            
    registry.register(SlowSensor, name="SlowSensor")
    # Run with short timeout
    results_timeout = await registry.analyze_all(audio, sr, timeout=0.5)
    
    if results_timeout["SlowSensor"]["reason"] == "Timeout":
        logger.info("Timeout logic verified: Sensor timed out as expected.")
    else:
        logger.error(f"Timeout logic failed: {results_timeout['SlowSensor']}")

    # 7. Verify Silence Handling (VocalTract)
    logger.info("Verifying silence handling...")
    silent_audio = np.zeros_like(audio)
    # Reset mocks to track calls
    librosa_mock.lpc.reset_mock()
    
    # We need to ensure VocalTractSensor uses the silent frame check
    # Since we mocked librosa, we can't easily test the *logic* inside the sensor 
    # without unmocking or complex mock setup. 
    # But we can check if it runs without crashing.
    vt_sensor = VocalTractSensor()
    vt_result = vt_sensor.analyze(silent_audio, sr)
    logger.info(f"Silence analysis result: {vt_result.passed}")
    
    # If our logic is correct, librosa.lpc should NOT be called for silent frames
    # But wait, the loop runs on frames. If all frames are silent, it should never call lpc.
    # Let's check call count.
    if librosa_mock.lpc.call_count == 0:
         logger.info("Silence handling verified: librosa.lpc was not called for silent audio.")
    else:
         logger.warning(f"Silence handling warning: librosa.lpc called {librosa_mock.lpc.call_count} times.")

    logger.info("Verification complete.")

if __name__ == "__main__":
    asyncio.run(verify_sensors())
