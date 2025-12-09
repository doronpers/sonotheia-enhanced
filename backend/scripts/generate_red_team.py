
#!/usr/bin/env python3
"""
Red Team Generator

Generates synthetic audio samples using various commercial text-to-speech APIs.
Usage:
    export ELEVENLABS_API_KEY="your_key"
    export OPENAI_API_KEY="your_key"
    python3 generate_red_team.py --service elevenlabs --count 10
"""

import os
import argparse
import logging
import random
import time
import json
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
# Script is at: backend/scripts/generate_red_team.py
# .env is at: .env (project root)
script_dir = Path(__file__).parent  # backend/scripts/
project_root = script_dir.parent.parent  # project root
env_path = project_root / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)  # override=True ensures .env values take precedence
else:
    # Fallback: try current directory and parent directories
    load_dotenv(override=True)  # Will search current dir and parents automatically

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("red_team_generator")

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

def generate_elevenlabs(text: str, filename: str):
    """Generate audio using ElevenLabs API."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not set. Skipping.")
        return False
        
    try:
        import requests
        
        # Default voice ID (Adam)
        voice_id = "pNInz6obpgDQGcFmaJgB" 
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            logger.error(f"ElevenLabs Error: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"ElevenLabs Exception: {e}")
        return False

def generate_openai(text: str, filename: str):
    """Generate audio using OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set. Skipping.")
        return False
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        response.stream_to_file(filename)
        return True
            
    except Exception as e:
        logger.error(f"OpenAI Exception: {e}")
        return False

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
