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
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation without API calls")
    
    args = parser.parse_args()
    
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
            filename = DEST_DIR / f"{service}_{timestamp}_{i}.mp3"
            
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
                # Respect rate limits
                time.sleep(1)
            else:
                logger.warning("Failed.")

if __name__ == "__main__":
    main()
