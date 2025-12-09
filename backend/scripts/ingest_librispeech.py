
#!/usr/bin/env python3
"""
Ingest LibriSpeech Data

Downloads and imports a subset of LibriSpeech dev-clean dataset for organic baselines.
"""

import shutil
import logging
import argparse
import tarfile
import random

import requests
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_librispeech")

# Config
DATA_URL = "https://www.openslr.org/resources/12/dev-clean.tar.gz"
TEMP_DIR = Path("backend/data/temp_librispeech")
DEST_DIR = Path("backend/data/library/organic")

# Ensure destination exists
DEST_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    """Download a file from a URL safely using streaming.

    This uses the `requests` library for better handling and provides progress updates.
    """
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(output_path, 'wb') as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    out_file.write(chunk)
                    t.update(len(chunk))
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            raise

def ingest_data(count: int = 50):
    logger.info("Starting LibriSpeech ingestion...")
    
    tar_path = TEMP_DIR / "dev-clean.tar.gz"
    
    # 1. Download if not exists
    if not tar_path.exists():
        logger.info(f"Downloading {DATA_URL}...")
        try:
            download_url(DATA_URL, str(tar_path))
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return

    # 2. Extract
    extract_dir = TEMP_DIR / "extracted"
    if not extract_dir.exists():
        logger.info("Extracting archive...")
        try:
            def safe_extract(tar_obj, path, members):
                """Extract tar safely, preventing path traversal attacks."""
                for member in members:
                    member_path = Path(path) / member.name
                    if not str(member_path.resolve()).startswith(str(Path(path).resolve())):
                        raise Exception("Path traversal attempt in tar file")
                tar_obj.extractall(path=path, members=members)

            with tarfile.open(tar_path, "r:gz") as tar:
                selected_members = tar.getmembers() # Get all members for extraction
                safe_extract(tar, extract_dir, selected_members)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return
            
    # 3. Find FLAC files
    flac_files = list(extract_dir.rglob("*.flac"))
    logger.info(f"Found {len(flac_files)} FLAC files.")
    
    # 4. Import random subset
    selected = random.sample(flac_files, min(count, len(flac_files)))
    
    success_count = 0
    for file_path in tqdm(selected, desc="Importing files"):
        dest_path = DEST_DIR / f"libri_{file_path.name}"
        if not dest_path.exists():
            shutil.copy2(file_path, dest_path)
            success_count += 1
            
    logger.info(f"Successfully imported {success_count} new organic samples from LibriSpeech.")
    
    # Cleanup
    if TEMP_DIR.exists():
        logger.info(f"Cleaning up temporary directory {TEMP_DIR}...")
        shutil.rmtree(TEMP_DIR)
        logger.info("Cleanup complete.") 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest LibriSpeech data")
    parser.add_argument("--count", type=int, default=50, help="Number of files to import")
    args = parser.parse_args()
    
    ingest_data(args.count)
