
import json
import os
from pathlib import Path

def main():
    library_dir = Path("/Volumes/Treehorn/Gits/sonotheia-enhanced/backend/data/library")
    organic_dir = library_dir / "organic"
    synthetic_dir = library_dir / "synthetic"
    
    # Analyze Organic (False Positives)
    organic_files = list(organic_dir.glob("*.json"))
    organic_total = len(organic_files)
    organic_failed = 0
    
    print(f"Scanning {organic_total} organic reports...")
    for f in organic_files:
        try:
            with open(f, 'r') as json_file:
                data = json.load(json_file)
                # If "passed" is False, it's a False Positive (since it's organic)
                if not data.get("passed", True):
                    organic_failed += 1
        except Exception:
            pass
            
    fpr = (organic_failed / organic_total) * 100 if organic_total > 0 else 0
    print(f"Organic Results: {organic_total - organic_failed}/{organic_total} passed.")
    print(f"False Positive Rate (FPR): {fpr:.2f}%")
    
    # Analyze Synthetic (True Positives)
    synthetic_files = list(synthetic_dir.glob("*.json"))
    synthetic_total = len(synthetic_files)
    synthetic_caught = 0
    
    print(f"Scanning {synthetic_total} synthetic reports...")
    for f in synthetic_files:
        try:
            with open(f, 'r') as json_file:
                data = json.load(json_file)
                # If "passed" is False, it's a True Positive (caught the fake)
                if not data.get("passed", True):
                    synthetic_caught += 1
        except Exception:
            pass

    tpr = (synthetic_caught / synthetic_total) * 100 if synthetic_total > 0 else 0
    print(f"Synthetic Results: {synthetic_caught}/{synthetic_total} caught.")
    print(f"True Positive Rate (TPR): {tpr:.2f}%")
    
    # Success Criteria
    if fpr < 5.0:
        print("\nSUCCESS: False Positive Rate is within acceptable limits (< 5%).")
        if fpr < 1.0:
            print("EXCELLENT: FPR is below 1%. Safe Mode is effective.")
    else:
        print(f"\nWARNING: False Positive Rate is high ({fpr:.2f}%). Thresholds may be too aggressive.")

if __name__ == "__main__":
    main()
