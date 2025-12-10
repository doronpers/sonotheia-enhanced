#!/usr/bin/env python3
"""
Recalibrate Thresholds Script

Parses existing analysis .json files to extract raw sensor metadata.
Calculates statistical distributions (Mean, StdDev, Percentiles) for Organic vs Synthetic.
Suggests new thresholds based on "Organic Acceptance" (e.g., 99th percentile of Organic).
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
import statistics

def load_data():
    library_dir = Path("backend/data/library")
    organic_dir = library_dir / "organic"
    synthetic_dir = library_dir / "synthetic"
    
    data = {
        "organic": defaultdict(list),
        "synthetic": defaultdict(list)
    }
    
    # Sensors to analyze mapping (Log Name -> Metadata Key)
    # We need to match the JSON output structure
    sensor_map = {
        "Pitch Velocity Sensor (Larynx Analysis)": "max_velocity_st_s",
        "Breath Sensor (Max Phonation)": "max_phonation_duration", # Need to verify key
        "Glottal Inertia Sensor": "violation_count",
        "Dynamic Range Sensor (Crest Factor)": "crest_factor", # Need to verify key
        "Bandwidth Sensor (Rolloff Frequency)": "rolloff_hz", # Need to verify key
        "Digital Silence Sensor": "lowest_energy_db" # Need to verify key
    }

    count = 0
    
    # Helper to parse directory
    def parse_dir(path, label):
        nonlocal count
        if not path.exists(): return
        
        for p in path.glob("*.json"):
            try:
                with open(p) as f:
                    res = json.load(f)
                
                physics = res.get("stage_results", {}).get("physics_analysis", {}).get("sensor_results", {})
                
                if count < 3:
                     print(f"DEBUG: Processing {p.name}")
                     print(f"DEBUG: Root keys: {list(res.keys())}")
                     print(f"DEBUG: Physics keys: {list(res.get('physics_analysis', {}).keys())}")
                     print(f"DEBUG: Sensor Results keys: {list(physics.keys())}")

                for sensor_name, result in physics.items():
                    # We accept partial matches for sensor names
                    key = None
                    target_meta = None
                    
                    if "Pitch Velocity" in sensor_name:
                        key = "pitch_velocity"
                        target_meta = "max_velocity_st_s"
                    elif "Breath" in sensor_name:
                        key = "breath"
                        target_meta = "value" # Usually value is the duration? Check metadata
                    elif "Glottal" in sensor_name:
                        key = "glottal_inertia"
                        target_meta = "violation_count" # metadata
                    elif "Dynamic Range" in sensor_name:
                        key = "dynamic_range"
                        target_meta = "value" # The score? No, likely just value. 
                    
                    # Extract raw value
                    val = None
                    if result.get("metadata") and target_meta in result["metadata"]:
                         val = result["metadata"][target_meta]
                    elif result.get("value") is not None:
                         # Fallback to main value if consistent with physical unit
                         val = result["value"]
                         
                    if val is not None and isinstance(val, (int, float)):
                        data[label][sensor_name].append(val)
                        
                count += 1
            except Exception:
                pass

    parse_dir(organic_dir, "organic")
    parse_dir(synthetic_dir, "synthetic")
    print(f"Parsed {count} files.")
    return data

def suggest_thresholds(data):
    print("\n" + "="*80)
    print(f"{'SENSOR NAME':<40} | {'ORG MEAN (STD)':<20} | {'SYN MEAN (STD)':<20} | {'SUGGESTED'}")
    print("="*80)
    
    for sensor, org_vals in data["organic"].items():
        syn_vals = data["synthetic"].get(sensor, [])
        
        if not org_vals: continue
        
        org_mean = np.mean(org_vals)
        org_std = np.std(org_vals)
        org_p95 = np.percentile(org_vals, 95)
        org_p99 = np.percentile(org_vals, 99)
        
        syn_str = "N/A"
        if syn_vals:
            syn_mean = np.mean(syn_vals)
            syn_std = np.std(syn_vals)
            syn_str = f"{syn_mean:.2f} ({syn_std:.2f})"
        
        # Heuristic for suggestion:
        # If higher is worse (e.g. Velocity, Violations): Threshold = P99 of Organic
        # If lower is worse (e.g. Bandwidth?): Logic needed.
        # Assuming higher = bad/feature for now for most physics violations.
        
        suggestion = org_p99
        
        print(f"{sensor[:38]:<40} | {org_mean:.2f} ({org_std:.2f})    | {syn_str:<20} | > {suggestion:.2f}")

if __name__ == "__main__":
    data = load_data()
    suggest_thresholds(data)
