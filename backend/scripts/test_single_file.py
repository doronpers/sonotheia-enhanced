
import sys
import json
import logging
from pathlib import Path
import os

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.detection.pipeline import DetectionPipeline
from backend.detection.config import get_default_config
from backend.sensors.utils import load_and_preprocess_audio
import io

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_single")

def test_file(file_path):
    print(f"Testing file: {file_path}")
    
    # Initialize pipeline
    cfg = get_default_config()
    cfg.demo_mode = False 
    pipeline = DetectionPipeline(config=cfg)
    
    # Load audio
    with open(file_path, "rb") as f:
        audio_io = io.BytesIO(f.read())
        audio_array, sr = load_and_preprocess_audio(audio_io)
        
    # Run detection
    result = pipeline.detect(audio_array, quick_mode=False)
    
    # Print key results
    fusion = result.get("fusion_result", {})
    physics = result.get("stage_results", {}).get("physics_analysis", {}).get("sensor_results", {})
    
    pitch_sensor = physics.get("Pitch Velocity Sensor (Larynx Analysis)", {})
    pitch_meta = pitch_sensor.get("metadata", {})
    
    print("\n" + "="*50)
    print("VERIFICATION RESULT")
    print("="*50)
    print(f"Decision:     {result.get('decision')}")
    print(f"Is Spoof:     {result.get('is_spoof')}")
    print(f"Score:        {result.get('detection_score'):.4f}")
    print("-" * 30)
    print(f"Risk Score:   {fusion.get('risk_score', 0):.4f}")
    print(f"Trust Score:  {fusion.get('trust_score', 0):.4f}")
    print("-" * 30)
    print("PITCH VELOCITY SENSOR:")
    print(f"  Passed:     {pitch_sensor.get('passed')}")
    print(f"  Value:      {pitch_sensor.get('score'):.4f} (Threshold: 0.5)")
    print(f"  Max Vel:    {pitch_meta.get('max_velocity_st_s', 0):.2f} st/s")
    print(f"  Threshold:  {pitch_sensor.get('detail', '').split('Limit: ')[-1].strip(').')}")
    print("="*50)

if __name__ == "__main__":
    test_file("backend/data/library/organic/libri_6313-66129-0005.flac")
