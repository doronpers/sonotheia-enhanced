
import os
import csv
import random
from pathlib import Path

def main():
    library_dir = Path("/Volumes/Treehorn/Gits/sonotheia-enhanced/backend/data/library")
    organic_dir = library_dir / "organic"
    synthetic_dir = library_dir / "synthetic"
    
    output_file = library_dir / "benchmark_metadata.csv"
    
    # Collect files
    organic_files = list(organic_dir.glob("*.flac")) + list(organic_dir.glob("*.wav")) + list(organic_dir.glob("*.mp3"))
    synthetic_files = list(synthetic_dir.glob("*.flac")) + list(synthetic_dir.glob("*.wav")) + list(synthetic_dir.glob("*.mp3"))
    
    # Sample 50 from each
    n_samples = 50
    selected_organic = random.sample(organic_files, min(len(organic_files), n_samples))
    selected_synthetic = random.sample(synthetic_files, min(len(synthetic_files), n_samples))
    
    print(f"Selected {len(selected_organic)} organic and {len(selected_synthetic)} synthetic files.")
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "label"])
        
        for file in selected_organic:
            # Path relative to library_dir
            rel_path = f"organic/{file.name}"
            writer.writerow([rel_path, 0])
            
        for file in selected_synthetic:
            rel_path = f"synthetic/{file.name}"
            writer.writerow([rel_path, 1])
            
    print(f"Written metadata to {output_file}")

if __name__ == "__main__":
    main()
