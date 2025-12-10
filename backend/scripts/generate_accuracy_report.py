#!/usr/bin/env python3
"""
Generate Accuracy Report
Parses .json results in backend/data/library to compute detection metrics.
"""

import json
from pathlib import Path
import sys
from collections import Counter

def calculate_metrics():
    library_dir = Path("backend/data/library")
    organic_dir = library_dir / "organic"
    synthetic_dir = library_dir / "synthetic"
    
    results = {
        "TP": 0, # Synthetic detected as Synthetic
        "TN": 0, # Organic detected as Organic
        "FP": 0, # Organic detected as Synthetic
        "FN": 0, # Synthetic detected as Organic
        "Errors": 0
    }
    
    details = []

    # 1. Analyze Organic (Ground Truth: REAL)
    if organic_dir.exists():
        for json_file in organic_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    
                # Decision logic
                is_spoof = data.get("is_spoof", False)
                score = data.get("detection_score", 0.0)
                
                if not is_spoof:
                    results["TN"] += 1
                else:
                    results["FP"] += 1
                    details.append(f"[FALSE POSITIVE] {json_file.name} (Score: {score:.4f})")
            except Exception:
                results["Errors"] += 1

    # 2. Analyze Synthetic (Ground Truth: PREDICTED FAKE)
    if synthetic_dir.exists():
        for json_file in synthetic_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    
                is_spoof = data.get("is_spoof", False)
                score = data.get("detection_score", 0.0)
                
                if is_spoof:
                    results["TP"] += 1
                else:
                    results["FN"] += 1
                    details.append(f"[FALSE NEGATIVE] {json_file.name} (Score: {score:.4f})")
            except Exception:
                results["Errors"] += 1

    # 3. Compute Stats
    total = results["TP"] + results["TN"] + results["FP"] + results["FN"]
    if total == 0:
        print("No results found.")
        return

    accuracy = (results["TP"] + results["TN"]) / total
    precision = results["TP"] / (results["TP"] + results["FP"]) if (results["TP"] + results["FP"]) > 0 else 0
    recall = results["TP"] / (results["TP"] + results["FN"]) if (results["TP"] + results["FN"]) > 0 else 0
    
    print("-" * 40)
    print(f"ACCURACY REPORT ({total} files)")
    print("-" * 40)
    print(f"Accuracy:  {accuracy*100:.2f}%")
    print(f"Precision: {precision*100:.2f}%")
    print(f"Recall:    {recall*100:.2f}%")
    print("-" * 40)
    print(f"True Positives (Caught Fakes): {results['TP']}")
    print(f"True Negatives (Cleared Real): {results['TN']}")
    print(f"False Positives (Real->Fake):  {results['FP']}")
    print(f"False Negatives (Fake->Real):  {results['FN']}")
    print("-" * 40)
    
    if details:
        print("\nTop Errors:")
        for err in details[:10]:
            print(err)

if __name__ == "__main__":
    calculate_metrics()
