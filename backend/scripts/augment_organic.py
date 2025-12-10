#!/usr/bin/env python3
"""
Organic Audio Augmenter

Applies telephony codec simulations (Landline, Mobile, VoIP) to existing organic audio files.
This creates a dataset of "Real but Degraded" audio to test robust physics detection.
"""

import sys
import argparse
import logging
from pathlib import Path
from tqdm import tqdm
import soundfile as sf
import numpy as np

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.telephony.pipeline import TelephonyPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("augment_organic")

ORGANIC_DIR = project_root / "backend/data/library/organic"

def process_file(file_path: Path, augment_types: list):
    """Apply augmentations to a single file."""
    try:
        # Check if this is already an augmented file to avoid re-augmenting
        if any(x in file_path.name for x in ["_landline", "_mobile", "_voip"]):
            return

        # Load audio (soundfile returns float64, pipe usually expects float32/ndarray)
        data, sr = sf.read(str(file_path))
        
        # Ensure mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)

        base_name = file_path.stem

        if "landline" in augment_types:
            out_path = file_path.parent / f"{base_name}_landline.wav"
            if not out_path.exists():
                processed = TelephonyPipeline.apply_landline_chain(data, sr)
                sf.write(str(out_path), processed, sr)

        if "mobile" in augment_types:
            out_path = file_path.parent / f"{base_name}_mobile.wav"
            if not out_path.exists():
                processed = TelephonyPipeline.apply_mobile_chain(data, sr)
                sf.write(str(out_path), processed, sr)

        if "voip" in augment_types:
            out_path = file_path.parent / f"{base_name}_voip.wav"
            if not out_path.exists():
                processed = TelephonyPipeline.apply_voip_chain(data, sr)
                sf.write(str(out_path), processed, sr)

    except Exception as e:
        logger.error(f"Failed to process {file_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Augment organic audio with telephony effects")
    parser.add_argument("--count", type=int, default=10, help="Number of files to process (default: 10)")
    parser.add_argument("--all", action="store_true", help="Process ALL organic files")
    parser.add_argument("--types", nargs="+", default=["landline", "mobile", "voip"], help="Augmentation types to apply")
    
    args = parser.parse_args()

    if not ORGANIC_DIR.exists():
        logger.error(f"Organic directory not found: {ORGANIC_DIR}")
        return

    # Gather candidate files (exclude existing temporary or augmentations)
    all_files = [
        f for f in ORGANIC_DIR.glob("*.flac") 
        if not any(x in f.name for x in ["_landline", "_mobile", "_voip"])
    ]
    
    if not all_files:
        # Fallback to wav if no flac
        all_files = [
            f for f in ORGANIC_DIR.glob("*.wav") 
            if not any(x in f.name for x in ["_landline", "_mobile", "_voip"])
        ]

    logger.info(f"Found {len(all_files)} organic source files.")

    # Select files to process
    if args.all:
        target_files = all_files
    else:
        # Randomly sample if count < total
        import random
        random.shuffle(all_files)
        target_files = all_files[:args.count]

    logger.info(f"Augmenting {len(target_files)} files with {args.types}...")

    # Process
    for f in tqdm(target_files, unit="file"):
        process_file(f, args.types)

    logger.info("Augmentation complete.")

if __name__ == "__main__":
    main()
