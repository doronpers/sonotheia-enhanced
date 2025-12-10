#!/usr/bin/env python3
"""
Micro Test Run Script

Randomly selects a subset of organic and synthetic files (default 50 each),
runs the detection pipeline on them, and reports accuracy.
Useful for quick verification of calibration changes.
"""

import sys
import argparse
import logging
import json
import random
from pathlib import Path
from tqdm import tqdm
import numpy as np

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.detection import get_pipeline, convert_numpy_types
from backend.sensors.utils import load_and_preprocess_audio
from backend.utils.config import load_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simplified format for test output
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("micro_test")

# Suppress other loggers
logging.getLogger("backend.detection").setLevel(logging.WARNING)

LIBRARY_DIR = Path("backend/data/library")

def get_files(label: str, count: int) -> list[Path]:
    """Get random subset of files from library."""
    dir_path = LIBRARY_DIR / label
    if not dir_path.exists():
        logger.warning(f"Directory {dir_path} does not exist.")
        return []
    
    # Filter for audio files (not json) - but we need to verify the audio exists
    # The library structure usually implies audio files are present or strictly handled.
    # We look for files that are NOT .json
    all_files = [f for f in dir_path.glob("*") if f.is_file() and f.suffix.lower() != ".json"]
    
    if len(all_files) <= count:
        return all_files
    
    return random.sample(all_files, count)

def run_test(count: int, update_library: bool = False):
    """Run the micro test."""
    print(f"============================================================")
    print(f"   MICRO TEST RUN (Target: {count} samples per class)")
    print(f"============================================================")
    
    organic_files = get_files("organic", count)
    synthetic_files = get_files("synthetic", count)
    
    print(f"Found {len(organic_files)} organic and {len(synthetic_files)} synthetic files.")
    
    # Combined list with expected labels
    test_set = [(f, False) for f in organic_files] + [(f, True) for f in synthetic_files]
    random.shuffle(test_set)
    
    # Initialize pipeline
    from backend.detection.config import get_default_config
    from backend.detection.pipeline import DetectionPipeline
    
    cfg = get_default_config()
    cfg.demo_mode = False
    pipeline = DetectionPipeline(config=cfg)
    
    results = {
        "TP": 0, "TN": 0, "FP": 0, "FN": 0,
        "errors": 0
    }
    
    details = []
    
    print("\nRunning analysis...")
    for file_path, is_synthetic in tqdm(test_set, unit="file"):
        try:
            # Detect directly from path to allow pipeline's loading fallbacks
            res = pipeline.detect(str(file_path), quick_mode=False)
            
            # Check correctness
            # The pipeline returns "is_spoof" (bool) and "detection_score" (float)
            detected_spoof = res.get("is_spoof", False)
            decision = res.get("decision", "UNKNOWN")
            score = res.get("detection_score", 0.0)
            
            # Extract Pitch Velocity for debug context
            pitch_vel = 0.0
            if "stage_results" in res and "physics_analysis" in res["stage_results"]:
                physics = res["stage_results"]["physics_analysis"]
                if "sensor_results" in physics:
                    pv = physics["sensor_results"].get("Pitch Velocity Sensor")
                    if pv:
                        pitch_vel = pv.get("score") or pv.get("value", 0.0)

            # Record detailed stat
            details.append({
                "file": file_path.name,
                "expected": "SPOOF" if is_synthetic else "REAL",
                "predicted": "SPOOF" if detected_spoof else "REAL",
                "decision": decision,
                "score": score,
                "pitch_vel": pitch_vel
            })
            
            if is_synthetic:
                if detected_spoof:
                    results["TP"] += 1
                else:
                    results["FN"] += 1
            else:
                if detected_spoof:
                    results["FP"] += 1
                else:
                    results["TN"] += 1
            
            # Optional: Update library JSON
            if update_library:
                json_path = file_path.with_suffix(".json")
                with open(json_path, "w") as f:
                    json.dump(convert_numpy_types(res), f, indent=2)
                    
        except Exception as e:
            logger.error(f"\nError processing {file_path.name}: {e}")
            results["errors"] += 1

    # Print Report
    total_organic = results["TN"] + results["FP"]
    total_synthetic = results["TP"] + results["FN"]
    
    precision = results["TP"] / (results["TP"] + results["FP"]) if (results["TP"] + results["FP"]) > 0 else 0
    recall = results["TP"] / (results["TP"] + results["FN"]) if (results["TP"] + results["FN"]) > 0 else 0
    accuracy = (results["TP"] + results["TN"]) / (total_organic + total_synthetic) if (total_organic + total_synthetic) > 0 else 0
    
    print("\n============================================================")
    print("   RESULTS SUMMARY")
    print("============================================================")
    print(f"Total Processed: {len(test_set)}")
    print(f"Errors:          {results['errors']}")
    print("------------------------------------------------------------")
    print(f"Accuracy:        {accuracy:.2%}")
    print(f"Precision:       {precision:.2%}")
    print(f"Recall:          {recall:.2%}")
    print("------------------------------------------------------------")
    print(f"True Positives (Caught Fakes): {results['TP']}")
    print(f"True Negatives (Cleared Real): {results['TN']}")
    print(f"False Positives (Real->Fake):  {results['FP']}")
    print(f"False Negatives (Fake->Real):  {results['FN']}")
    print("============================================================")
    
    if results["FP"] > 0:
        print("\nFalse Positives (Top 5):")
        fps = [d for d in details if d["expected"] == "REAL" and d["predicted"] == "SPOOF"]
        for fp in fps[:5]:
             print(f"- {fp['file']} (Score: {fp['score']:.2f}, Dec: {fp['decision']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Micro Test Run")
    parser.add_argument("--count", type=int, default=50, help="Samples per class")
    parser.add_argument("--update", action="store_true", help="Update library JSON files")
    args = parser.parse_args()
    
    run_test(args.count, args.update)
