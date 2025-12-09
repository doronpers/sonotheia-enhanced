
#!/usr/bin/env python3
"""
Ingest ASVspoof 2021 Data

Reads the metadata key file and imports a balanced subset of files into the Lab.
"""

import shutil
import logging
import argparse
import random
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_asvspoof")

# Config
KEY_FILE = Path("backend/data/keys/DF/CM/trial_metadata.txt")
SOURCE_AUDIO_DIR = Path("/Volumes/Treehorn/Gits/Audio Deepfakes Files and Font/ASVspoof2021_DF_eval/flac")
DEST_DIR = Path("backend/data/library")

# Ensure destination exists
(DEST_DIR / "organic").mkdir(parents=True, exist_ok=True)
(DEST_DIR / "synthetic").mkdir(parents=True, exist_ok=True)

def ingest_data(count: int = 50):
    if not KEY_FILE.exists():
        logger.error(f"Key file not found at {KEY_FILE}")
        return
        
    if not SOURCE_AUDIO_DIR.exists():
        logger.error(f"Source audio directory not found at {SOURCE_AUDIO_DIR}")
        return

    logger.info("Reading metadata...")
    
    bonafide_files = []
    spoof_files = []
    
    with open(KEY_FILE, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
                
            # Column 2 is filename, Column 6 is label (spoof/bonafide)
            filename = parts[1] + ".flac"
            label = parts[5]
            
            if label == "bonafide":
                bonafide_files.append(filename)
            elif label == "spoof":
                spoof_files.append(filename)

    logger.info(f"Found {len(bonafide_files)} organic and {len(spoof_files)} synthetic files.")
    
    # Select subset
    selected_organic = random.sample(bonafide_files, min(count, len(bonafide_files)))
    selected_synthetic = random.sample(spoof_files, min(count, len(spoof_files)))
    
    # Copy files
    def copy_files(file_list, target_label):
        dest_folder = DEST_DIR / target_label
        successful = 0
        for filename in tqdm(file_list, desc=f"Importing {target_label}"):
            src = SOURCE_AUDIO_DIR / filename
            dst = dest_folder / filename
            
            if src.exists():
                if not dst.exists():
                    shutil.copy2(src, dst)
                    successful += 1
            else:
                logger.warning(f"Source file missing: {src}")
        return successful

    organic_count = copy_files(selected_organic, "organic")
    synthetic_count = copy_files(selected_synthetic, "synthetic")
    
    logger.info(f"Ingestion complete. Imported {organic_count} organic and {synthetic_count} synthetic files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest ASVspoof data")
    parser.add_argument("--count", type=int, default=50, help="Number of files per class")
    args = parser.parse_args()
    
    ingest_data(args.count)
