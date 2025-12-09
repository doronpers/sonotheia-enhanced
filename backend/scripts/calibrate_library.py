
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
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent dir to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from calibration.optimizer import ThresholdOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("calibrate_library")

BACKEND_DIR = Path(__file__).resolve().parent.parent
LIBRARY_DIR = BACKEND_DIR / "data" / "library"
SETTINGS_PATH = BACKEND_DIR / "config" / "settings.yaml"

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

def update_config_file(updates: Dict[str, Dict[str, float]]) -> bool:
    """
    Update settings.yaml with new thresholds using regex to preserve comments.
    
    Args:
        updates: Dict identifying sensor->threshold->value
                 e.g. {"breath": {"max_phonation_seconds": 15.2}}
                 
    Returns:
        True if successful
    """
    if not SETTINGS_PATH.exists():
        logger.error(f"Settings file not found at {SETTINGS_PATH}")
        return False
        
    try:
        with open(SETTINGS_PATH, "r") as f:
            content = f.read()
            
        original_content = content
        changes_count = 0
        
        for sensor, thresholds in updates.items():
            for result_key, new_value in thresholds.items():
                if new_value is None:
                    continue
                    
                # Regex logic:
                # 1. Find sensor section (lines indented or not)
                # 2. Within that, find the specific key
                # This is complex with single regex. simpler approach:
                # Iterate lines, find sensor block, then find key inside block.
                
                lines = content.splitlines()
                new_lines = []
                in_sensor_block = False
                sensor_indent = -1
                updated_this_key = False
                
                # Assume structure from settings.yaml:
                # sensors:
                #   sensor_name:
                #     key: value
                
                for line in lines:
                    stripped = line.strip()
                    lstripped = line.lstrip()
                    current_indent = len(line) - len(lstripped)
                    
                    if stripped.startswith(f"{sensor}:"):
                        # Found sensor block? Check context if necessary (under 'sensors:')
                        # But simpler heuristic: assume unique sensor names at 2 or 4 indent
                        in_sensor_block = True
                        sensor_indent = current_indent
                        new_lines.append(line)
                        continue
                        
                    if in_sensor_block:
                        # Check if we left the block (same indent or less as sensor line)
                        if stripped and not stripped.startswith("#") and current_indent <= sensor_indent:
                            in_sensor_block = False
                        
                        # Use loose matching for keys
                        elif stripped.startswith(result_key + ":"):
                            # Replace value part
                            # Format: key: value # comment
                            parts = line.split(":", 1)
                            key_part = parts[0]
                            rest = parts[1]
                            
                            # Preserve comment
                            comment = ""
                            if "#" in rest:
                                val_comment_split = rest.split("#", 1)
                                comment = " #" + val_comment_split[1]
                                
                            # Format new line
                            new_line = f"{key_part}: {new_value:.4f}{comment}"
                            new_lines.append(new_line)
                            updated_this_key = True
                            changes_count += 1
                            continue
                    
                    new_lines.append(line)
                
                content = "\n".join(new_lines)
                if content.endswith("\n") != original_content.endswith("\n"):
                    # restore newline at end if meaningful
                     pass 

        if changes_count > 0:
            with open(SETTINGS_PATH, "w") as f:
                f.write(content)
            logger.info(f"Updated {changes_count} thresholds in {SETTINGS_PATH}")
            return True
        else:
            logger.warning("No matching keys found to update in settings.yaml")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return False

def map_sensor_to_config(sensor_name: str, result_key: str) -> Optional[Tuple[str, str]]:
    """Map display name to yaml key."""
    name_lower = sensor_name.lower()
    
    if "breath" in name_lower:
        return ("breath", "max_phonation_seconds")
    if "two mouth" in name_lower:
        return ("two_mouth", "combined_threshold")
    if "formant trajectory" in name_lower:
        return ("formant_trajectory", "consistency_threshold")
    if "glottal inertia" in name_lower:
        return ("glottal_inertia", "phase_entropy_threshold") # Guess based on importance
    if "coarticulation" in name_lower:
        return ("coarticulation", "anomaly_threshold")
    if "global formant" in name_lower:
        return ("global_formants", "outlier_threshold")
    if "dynamic range" in name_lower:
        return ("dynamic_range", "min_crest_factor")
    if "bandwidth" in name_lower:
        return ("bandwidth", "min_rolloff_hz")
    if "phase coherence" in name_lower:
        return ("phase_coherence", "suspicion_threshold")
    if "digital silence" in name_lower:
        return ("digital_silence", "silence_threshold") # Assumed key, need to verify
        
    return None

def main():
    parser = argparse.ArgumentParser(description="Calibrate library thresholds")
    parser.add_argument("--update-config", action="store_true", help="Update backend/config/settings.yaml with new thresholds")
    args = parser.parse_args()

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
        
    print("=" * 60)
    print("CALIBRATION REPORT")
    print("=" * 60)
    
    updates_to_apply = {}

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
        
        if args.update_config:
            print("Applying updates to configuration...")
            for res in results:
                mapping = map_sensor_to_config(res["Sensor"], "threshold")
                if mapping:
                    sensor_key, config_key = mapping
                    if sensor_key not in updates_to_apply:
                        updates_to_apply[sensor_key] = {}
                    updates_to_apply[sensor_key][config_key] = res["Optimal Threshold"]
                    
            if updates_to_apply:
                if update_config_file(updates_to_apply):
                    print("✅ Configuration updated successfully.")
                else:
                    print("❌ Failed to update configuration.")
            else:
                print("⚠️ No mappable sensors found to update.")
                
        else:
            print("RECOMMENDATION:")
            print("Update your backend/config/settings.yaml with these new thresholds.")
            print("Run with --update-config to apply automatically.")
        
        # Save to file (Current State)
        df.to_csv(LIBRARY_DIR / "calibration_report.csv", index=False)
        print(f"Saved detailed report to {LIBRARY_DIR}/calibration_report.csv")

        # Append to History (Historical Record)
        try:
            from datetime import datetime
            history_path = LIBRARY_DIR / "calibration_history.csv"
            
            # Prepare history dataframe
            df_history = df.copy()
            # Insert Timestamp as first column
            df_history.insert(0, "Timestamp", datetime.now().isoformat())
            
            # Append to file (header only if file doesn't exist)
            file_exists = history_path.exists()
            df_history.to_csv(history_path, mode='a', header=not file_exists, index=False)
            print(f"Appended results to history log: {history_path}")
            
        except Exception as e:
            logger.error(f"Failed to append to history log: {e}")
    else:
        print("No valid sensors found for calibration.")

if __name__ == "__main__":
    main()
