#!/usr/bin/env python3
"""
Red Team Generator

Generates synthetic audio samples using various commercial text-to-speech APIs.
Usage:
    export ELEVENLABS_API_KEY="your_key"
    export OPENAI_API_KEY="your_key"
    python3 generate_red_team.py --service elevenlabs --count 10
"""

import argparse
import logging
import random
import time
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("red_team_generator")

# Ensure project root is in sys.path for 'backend' imports
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import shared TTS utilities
from tts_utils import load_env_file, generate_elevenlabs, generate_openai

# Load environment variables from project root
load_env_file(Path(__file__))

# Config
PROMPTS_FILE = Path("backend/data/red_team_prompts.txt")
DEST_DIR = Path("backend/data/library/synthetic")
DEST_DIR.mkdir(parents=True, exist_ok=True)


def load_prompts() -> List[str]:
    if not PROMPTS_FILE.exists():
        logger.warning("Prompts file not found. Using defaults.")
        return ["The quick brown fox jumps over the lazy dog.", "Authentication test 123."]

    with open(PROMPTS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="Generate Red Team deepfakes")
    parser.add_argument("--service", choices=["elevenlabs", "openai", "all"], default="all", help="TTS Service")
    parser.add_argument("--count", type=int, default=5, help="Number of files to generate per service")
    parser.add_argument("--augment", action="store_true", help="Generate telephony variants (Landline, Mobile, VoIP)")
    
    args = parser.parse_args()
    
    # Lazy import to avoid breaking if dependencies missing during dry run
    if args.augment:
        try:
            import soundfile as sf
            from backend.telephony.pipeline import TelephonyPipeline
        except ImportError as e:
            logger.error(f"Augmentation requires 'soundfile' and 'backend' package: {e}")
            return

    prompts = load_prompts()
    
    if args.dry_run:
        logger.info("DRY RUN: No actual API calls will be made.")
    
    services = []
    if args.service == "all":
        services = ["elevenlabs", "openai"]
    else:
        services = [args.service]
        
    for service in services:
        logger.info(f"Generating {args.count} samples using {service}...")
        
        for i in range(args.count):
            prompt = random.choice(prompts)
            timestamp = int(time.time())
            base_filename = DEST_DIR / f"{service}_{timestamp}_{i}"
            filename = base_filename.with_suffix(".mp3")
            
            logger.info(f"[{i+1}/{args.count}] Generating: '{prompt[:30]}...' -> {filename.name}")
            
            if args.dry_run:
                # Create dummy file
                with open(filename, "w") as f:
                    f.write("dummy content")
                continue
                
            success = False
            if service == "elevenlabs":
                success = generate_elevenlabs(prompt, str(filename))
            elif service == "openai":
                success = generate_openai(prompt, str(filename))
                
            if success:
                logger.info("Success.")
                
                # --- Telephony Augmentation ---
                if args.augment:
                    try:
                        logger.info("  Generating telephony variants...")
                        # 1. Load original
                        data, sr = sf.read(str(filename))
                        
                        # 2. Landline
                        landline_audio = TelephonyPipeline.apply_landline_chain(data, sr)
                        sf.write(str(base_filename) + "_landline.wav", landline_audio, sr)
                        
                        # 3. Mobile
                        mobile_audio = TelephonyPipeline.apply_mobile_chain(data, sr)
                        sf.write(str(base_filename) + "_mobile.wav", mobile_audio, sr)
                        
                        # 4. VoIP
                        voip_audio = TelephonyPipeline.apply_voip_chain(data, sr)
                        sf.write(str(base_filename) + "_voip.wav", voip_audio, sr)
                        
                    except Exception as e:
                        logger.error(f"  Augmentation failed: {e}")
                # ------------------------------

                # Respect rate limits
                time.sleep(1)
            else:
                logger.warning("Failed.")

if __name__ == "__main__":
    main()
