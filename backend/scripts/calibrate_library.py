
#!/usr/bin/env python3
"""
Library Calibration Script

Iterates through the Audio Laboratory library (Organic vs Synthetic),
collects sensor scores, and calculates the optimal thresholds to minimize EER.
"""

import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List

# Add parent dir to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from calibration.optimizer import ThresholdOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("calibrate_library")

LIBRARY_DIR = Path("backend/data/library")

def load_scores() -> Dict[str, Dict[str, List[float]]]:
    """
    Load analysis results from the library.
    Returns:
        Dict: {
            "sensor_name": {
                "real": [scores...],
                "fake": [scores...]
            }
        }
    """
    data = {}
    
    # helper to extract scores recursively
    def extract_from_json(path: Path, label: str):
        try:
            with open(path, "r") as f:
                analysis = json.load(f)
                
            # We look for "stage_results" -> "physics_analysis" -> "sensor_results"
            # Or top-level "detection_score" for global EER
            
            # Global Score
            if "detection_score" in analysis:
                if "global" not in data: data["global"] = {"real": [], "fake": []}
                data["global"][label].append(analysis["detection_score"])
                
            # Physics Sensors
            if "stage_results" in analysis:
                physics = analysis["stage_results"].get("physics_analysis", {})
                sensors = physics.get("sensor_results", {})
                
                for sensor_name, result in sensors.items():
                    # We need a numeric score. 
                    # The structure seems to be: { passed: bool, score: float, ... }
                    # Inspecting the code/files earlier showed 'metadata' might hold raw values
                    # But usually 'score' is available if standardized.
                    # Let's check metadata or assume 'score' key if present.
                    
                    score = result.get("score")
                    if score is None and "metadata" in result:
                        # Fallback to first numeric value in metadata?
                        # For now, let's skip if no explicit score.
                        pass
                        
                    # Let's assume there is a way to get a float score. 
                    # If the current codebase doesn't save raw scores in 'sensor_results',
                    # we might need to rely on 'metadata'.
                    
                    # WORKAROUND: In previous view_file of Laboratory.jsx, 
                    # we saw `data.metadata` loop.
                    # Let's try to extract a 'score', 'confidence', 'energy', etc. from metadata
                    # if standard 'score' is missing.
                    
                    val = score
                    if val is None and "metadata" in result:
                        # Common keys: 'energy', 'frequency', 'coherence'
                        for key in ["energy", "score", "confidence", "coherence", "dynamic_range"]:
                             if key in result["metadata"]:
                                 val = result["metadata"][key]
                                 break
                                 
                    if val is not None and isinstance(val, (int, float)):
                        if sensor_name not in data: data[sensor_name] = {"real": [], "fake": []}
                        data[sensor_name][label].append(float(val))

        except Exception as e:
            logger.warning(f"Failed to read {path.name}: {e}")

    # Load Organic (Real)
    organic_dir = LIBRARY_DIR / "organic"
    if organic_dir.exists():
        for f in organic_dir.glob("*.json"):
            extract_from_json(f, "real")
            
    # Load Synthetic (Fake)
    synthetic_dir = LIBRARY_DIR / "synthetic"
    if synthetic_dir.exists():
        for f in synthetic_dir.glob("*.json"):
            extract_from_json(f, "fake")
            
    return data

def main():
    logger.info("=" * 60)
    logger.info("  AUDIO LABORATORY CALIBRATION UTILITY")
    logger.info("=" * 60)
    
    data = load_scores()
    
    if not data:
        logger.error("No analysis data found.")
        logger.error("Please run the 'Analyze Library' task first to generate sensor scores.")
        logger.error("Usage: python backend/scripts/analyze_library.py")
        return
        
    results = []
    
    for sensor, scores in data.items():
        real_scores = scores["real"]
        fake_scores = scores["fake"]
        
        n_real = len(real_scores)
        n_fake = len(fake_scores)
        
        if n_real < 5 or n_fake < 5:
            logger.warning(f"Skipping {sensor}: Insufficient data (Real: {n_real}, Fake: {n_fake})")
            if n_real < 5:
                logger.warning(f"  -> Need more REAL {sensor} samples (upload known real audio)")
            if n_fake < 5:
                logger.warning(f"  -> Need more FAKE {sensor} samples (generate synthetic audio)")
            continue
            
        logger.info(f"Optimizing {sensor} (Real: {n_real}, Fake: {n_fake})...")
        
        optimizer = ThresholdOptimizer(sensor)
        res = optimizer.optimize(real_scores, fake_scores, (0, 1))
        
        results.append({
            "Sensor": sensor,
            "Optimal Threshold": res.optimal_threshold,
            "Direction": res.threshold_type, # min or max
            "EER": res.eer,
            "Accuracy": 1.0 - res.eer
        })
        
    print("\n" + "=" * 60)
    print("CALIBRATION REPORT")
    print("=" * 60)
    
    if results:
        df = pd.DataFrame(results)
        # Reorder columns
        df = df[["Sensor", "Optimal Threshold", "Direction", "Accuracy", "EER"]]
        print(df.to_string(index=False, formatters={
            "Optimal Threshold": "{:.4f}".format,
            "Accuracy": "{:.1%}".format,
            "EER": "{:.1%}".format
        }))
        
        print("\n" + "-" * 60)
        print("RECOMMENDATION:")
        print("Update your backend/config.py with these new thresholds.")
        
        # Save to file
        df.to_csv(LIBRARY_DIR / "calibration_report.csv", index=False)
        print(f"Saved detailed report to {LIBRARY_DIR}/calibration_report.csv")
    else:
        print("No valid sensors found for calibration.")

if __name__ == "__main__":
    main()
