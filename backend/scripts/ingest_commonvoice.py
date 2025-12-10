
#!/usr/bin/env python3
"""
Ingest Mozilla Common Voice Data

Imports organic baselines from Common Voice.
NOTE: Common Voice requires authentication/agreement. This script attempts to use
the HuggingFace `datasets` library if HUGGINGFACE_TOKEN is present, or looks for
a local tar.gz file.
"""

import os
import shutil
import logging
import argparse
import tarfile
import random
from pathlib import Path
from tqdm import tqdm

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root
    script_dir = Path(__file__).parent  # backend/scripts/
    project_root = script_dir.parent.parent  # project root
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not installed, will use system environment variables
except Exception:
    pass  # Ignore .env loading errors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_commonvoice")

# Config
DEST_DIR = Path("backend/data/library/organic")
LOCAL_ARCHIVE_PATH = Path("backend/data/cv-corpus.tar.gz") # User must place file here if not using HF

# Ensure destination exists
DEST_DIR.mkdir(parents=True, exist_ok=True)

def ingest_from_local(archive_path: Path, count: int):
    """Ingest from a manually downloaded Common Voice archive."""
    if not archive_path.exists():
        logger.error(f"Local archive not found at {archive_path}")
        logger.info("Please download Common Voice dataset and place it at backend/data/cv-corpus.tar.gz")
        return

    logger.info(f"Extracting metadata from {archive_path}...")
    
    # Create temp extraction dir
    extract_dir = Path("backend/data/temp_cv")
    extract_dir.mkdir(exist_ok=True)
    
    try:
        # Extract MP3s (Common Voice is usually MP3)
        with tarfile.open(archive_path, "r:gz") as tar:
            # Only extract a subset if possible, but reading tar is sequential.
            # We'll extract all for simplicity or look for mp3 extension
            members = []
            for member in tar:
                if member.name.endswith(".mp3"):
                    members.append(member)
            
            # Select random subset to extract
            selected_members = random.sample(members, min(count * 2, len(members)))
            
            # Safely extract selected members to prevent path traversal
            def safe_extract(tar_obj, path, members):
                """Safely extract given members, preventing path traversal attacks."""
                for member in members:
                    member_path = Path(path) / member.name
                    if not str(member_path.resolve()).startswith(str(Path(path).resolve())):
                        raise Exception("Path traversal attempt in tar file")
                tar_obj.extractall(path=path, members=members)

            safe_extract(tar, extract_dir, selected_members)
            
        # Find extracted files
        mp3_files = list(extract_dir.rglob("*.mp3"))
        logger.info(f"Extracted {len(mp3_files)} MP3 files.")
        
        # Import
        selected = random.sample(mp3_files, min(count, len(mp3_files)))
        
        success_count = 0
        for file_path in tqdm(selected, desc="Importing Common Voice"):
            dest_path = DEST_DIR / f"cv_{file_path.name}"
            # Copy (mp3 is supported by our pipeline via librosa/ffmpeg)
            shutil.copy2(file_path, dest_path)
            success_count += 1
            
        logger.info(f"Successfully imported {success_count} samples from Common Voice.")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
    finally:
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

def ingest_from_huggingface(count: int, lang: str = "en"):
    """Ingest using Hugging Face datasets (requires token)."""
    token = os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        logger.error("HUGGINGFACE_TOKEN not set. Cannot download from Hub.")
        return

    try:
        from datasets import load_dataset
        import soundfile as sf
        
        logger.info(f"Loading Common Voice ({lang}) from Hugging Face...")
        # Try different Common Voice dataset versions
        dataset_names = [
            "fsicoli/common_voice_22_0",  # Reliable mirror
            "fsicoli/common_voice_18_0",
            "mozilla-foundation/common_voice_11_0"
        ]
        ds = None
        last_error = None
        for dataset_name in dataset_names:
            try:
                logger.info(f"Trying dataset: {dataset_name}")
                ds = load_dataset(dataset_name, lang, split=f"train[:{count}]", token=token, streaming=True, revision="main")
                logger.info(f"Successfully loaded {dataset_name}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {dataset_name}: {e}") # Changed to warning to be visible
                last_error = e
                continue
        
        if ds is None:
            raise Exception(f"Could not load any Common Voice dataset version. Last error: {last_error}")
        
        success_count = 0
        for i, item in enumerate(tqdm(ds.take(count), total=count, desc="Downloading streams")):
            audio_array = item["audio"]["array"]
            sr = item["audio"]["sampling_rate"]
            
            # Save as WAV/FLAC (better than MP3 for analysis)
            filename = f"cv_stream_{i}.flac"
            dest_path = DEST_DIR / filename
            
            sf.write(str(dest_path), audio_array, sr)
            success_count += 1
            
        logger.info(f"Successfully streamed and saved {success_count} samples from Hugging Face.")
        
    except ImportError:
        logger.error("datasets library not installed. Run `pip install datasets`.")
    except Exception as e:
        logger.error(f"HF Download failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Common Voice data")
    parser.add_argument("--count", type=int, default=50, help="Number of files to import")
    parser.add_argument("--local", action="store_true", help="Use local archive instead of Hugging Face")
    parser.add_argument("--path", type=str, default="backend/data/cv-corpus.tar.gz", help="Path to local archive")
    
    args = parser.parse_args()
    
    if args.local or os.path.exists(args.path):
        ingest_from_local(Path(args.path), args.count)
    else:
        logger.info("Local archive not found/specified. Attempting Hugging Face download...")
        ingest_from_huggingface(args.count)
