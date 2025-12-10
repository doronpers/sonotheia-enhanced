
import sys
import os
import json
import logging
import asyncio
from pathlib import Path
from tqdm import tqdm

# Add parent to path
sys.path.append(os.getcwd())

from backend.detection.pipeline import DetectionPipeline
from backend.detection.config import get_default_config
from backend.sensors.utils import load_and_preprocess_audio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("synthetic_test")

def main():
    # Load unanalyzed files from file
    batch_file = Path("unanalyzed_batch.txt")
    if not batch_file.exists():
        print("Error: unanalyzed_batch.txt not found")
        return

    with open(batch_file, "r") as f:
        files = [line.strip() for line in f.readlines() if line.strip()]

    print(f"Loaded {len(files)} files for testing.")
    
    # Initialize Pipeline (PROD MODE)
    cfg = get_default_config()
    cfg.demo_mode = False 
    pipeline = DetectionPipeline(config=cfg)
    
    detected_fakes = 0
    total = 0
    
    results_dir = Path("backend/data/library/synthetic")
    
    for file_path_str in tqdm(files, desc="Testing Synthetics"):
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
            
        try:
            # Detect directly from path (let pipeline handle loading)
            result = pipeline.detect(str(file_path), quick_mode=False)
            
            # Check verdict
            # passed=True means it thinks it's REAL (Fail for us)
            # passed=False means it thinks it's FAKE (Success for us)
            # The result dict has "is_spoof" key: True=FAKE, False=REAL
            is_fake_detected = result.get("is_spoof", False)
            score = result.get('detection_score', 0.0)
            
            if is_fake_detected:
                detected_fakes += 1
            else:
                # Only log valid analysis failures (score > 0.0)
                if score > 0.0001:
                    print(f"\n[VALID FAILURE] {file_path.name}", flush=True)
                    print(f"  Final Score: {score:.4f}", flush=True)
                    print(f"  Decision: {result.get('decision', 'UNKNOWN')}", flush=True)
                    
                    # Print Fusion Details
                    if 'fusion_result' in result:
                        fr = result['fusion_result']
                        print(f"  Risk Score: {fr.get('risk_score', 0.0):.4f}", flush=True)
                        print(f"  Trust Score: {fr.get('trust_score', 0.0):.4f}", flush=True)
                        
                        if 'stage_scores' in fr:
                            print("  Stage Scores:", flush=True)
                            for stage, s_score in fr['stage_scores'].items():
                                print(f"    - {stage}: {s_score:.4f}", flush=True)
                    
                    # Print Physics Breakdown
                    if 'stage_results' in result and 'physics_analysis' in result['stage_results']:
                        physics = result['stage_results']['physics_analysis']
                        if 'sensor_results' in physics:
                            print("  Physics Sensors:", flush=True)
                            for s_name, s_res in physics['sensor_results'].items():
                                if s_res and 'score' in s_res:
                                    print(f"    - {s_name}: {s_res['score']:.4f}", flush=True)
                                elif s_res and 'value' in s_res:
                                    val = s_res['value']
                                    # Try to interpret value if score missing
                                    if isinstance(val, (int, float)):
                                         print(f"    - {s_name}: {val:.4f} (Raw Value)", flush=True)
                else:
                    # Minimal log for load errors
                    pass
            
            total += 1
            
            # Optional: Save JSON to not waste the work
            # result_path = file_path.with_suffix(".json")
            # with open(result_path, "w") as f:
            #    from backend.detection import convert_numpy_types
            #    json.dump(convert_numpy_types(result), f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed {file_path.name}: {e}")
            
    if total > 0:
        tpr = (detected_fakes / total) * 100
        print("\n" + "="*40)
        print(f"RESULTS (Batch of {total})")
        print("="*40)
        print(f"Detected Fakes (TPR): {detected_fakes}/{total} ({tpr:.2f}%)")
        print("="*40)
        
        if tpr > 0:
            print("SUCCESS: Calibration is detecting fakes.")
        else:
            print("WARNING: Still 0% detection. Thresholds might still be too loose.")
    else:
        print("No files processed.")

if __name__ == "__main__":
    main()
