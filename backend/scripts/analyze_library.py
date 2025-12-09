
#!/usr/bin/env python3
"""
Analyze Library Script

Batch-processes the library directory to generate analysis reports for all files.
Useful if files were manually added to the backend/data/library folders.
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from tqdm import tqdm

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.detection import get_pipeline, convert_numpy_types
from backend.sensors.utils import load_and_preprocess_audio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analyze_library")

LIBRARY_DIR = Path("backend/data/library")

def analyze_directory(label: str, force: bool = False):
    """Analyze all files in a specific library subdirectory."""
    dir_path = LIBRARY_DIR / label
    if not dir_path.exists():
        logger.warning(f"Directory {dir_path} does not exist.")
        return

    files = [f for f in dir_path.glob("*") if f.is_file() and f.suffix != ".json"]
    
    logger.info(f"Found {len(files)} files in {label} library.")
    
    pipeline = get_pipeline()
    
    for file_path in tqdm(files, desc=f"Analyzing {label}"):
        result_path = file_path.with_suffix(".json")
        
        if result_path.exists() and not force:
            continue
            
        try:
            # Load and preprocess
            with open(file_path, "rb") as f:
                import io
                audio_io = io.BytesIO(f.read())
                audio_array, sr = load_and_preprocess_audio(audio_io)
            
            # Run pipeline
            result = pipeline.detect(audio_array, quick_mode=False)
            
            # Save result
            with open(result_path, "w") as f:
                json.dump(convert_numpy_types(result), f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to analyze {file_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Analyze audio library.")
    parser.add_argument("--force", action="store_true", help="Re-analyze files even if report exists")
    parser.add_argument("--label", choices=["organic", "synthetic", "all"], default="all", help="Which subset to analyze")
    
    args = parser.parse_args()
    
    if args.label in ["organic", "all"]:
        analyze_directory("organic", args.force)
        
    if args.label in ["synthetic", "all"]:
        analyze_directory("synthetic", args.force)
        
    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()
