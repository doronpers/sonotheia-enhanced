#!/usr/bin/env python3
"""
Generate Phonetically Diverse Voice Samples

Creates voice samples using phrases that maximize phonetic coverage for deepfake detection training.
Covers all major English phonemes, diphthongs, consonant clusters, and stress patterns.

Usage:
    export ELEVENLABS_API_KEY="your_key"
    export OPENAI_API_KEY="your_key"
    python3 generate_phonetic_samples.py --service elevenlabs --count 50 --output-dir backend/data/library/phonetic
"""

import os
import argparse
import logging
import json
import time
from pathlib import Path
from typing import List, Dict

# Try to load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use system environment variables

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("phonetic_generator")

# Check for required dependencies at startup
def check_dependencies():
    """Check if required dependencies are available and provide helpful error messages."""
    missing = []
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    try:
        from openai import OpenAI
    except ImportError:
        missing.append("openai")
    
    if missing:
        logger.warning("=" * 60)
        logger.warning("Missing dependencies detected:")
        for dep in missing:
            logger.warning(f"  - {dep}")
        logger.warning("")
        logger.warning("To fix this:")
        logger.warning("  1. Activate the virtual environment:")
        logger.warning("     source backend/venv/bin/activate")
        logger.warning("  2. Or install dependencies:")
        logger.warning(f"     pip install {' '.join(missing)}")
        logger.warning("=" * 60)
        logger.warning("")
        logger.warning("The script will continue but API calls will fail.")
        logger.warning("")
    
    return len(missing) == 0

# Phonetically diverse phrases designed to maximize sound combination coverage
# Organized by phonetic features they emphasize

PHONETIC_PHRASES = [
    # Vowels - All major vowel sounds
    "The quick brown fox jumps over the lazy dog",  # Short vowels: a, e, i, o, u
    "She sells seashells by the seashore",  # Long e, sh, s clusters
    "How now brown cow",  # Diphthongs: ow, ou
    "The rain in Spain stays mainly in the plain",  # Long a, ai diphthong
    "Peter Piper picked a peck of pickled peppers",  # P alliteration, short i, e
    "Red lorry, yellow lorry",  # R, L sounds, o sounds
    "Unique New York",  # U, ew sounds, n clusters
    "Toy boat",  # Diphthongs: oy, oa
    
    # Consonant clusters - Complex combinations
    "The sixth sick sheik's sixth sheep's sick",  # Th, s, sh, k clusters
    "Three free throws",  # Th, r, fr clusters
    "Black background, brown background",  # Bl, br, ck, gr clusters
    "Greek grapes",  # Gr, gr clusters
    "Fresh fried fish",  # Fr, sh, f clusters
    "Six slippery snails slid slowly seaward",  # S, sl, sn, sw clusters
    "Theophilus Thistle, the successful thistle-sifter",  # Th, st, ss clusters
    "Twelve twins twirled twelve twigs",  # Tw, tw clusters
    
    # Nasals and liquids
    "Round and round the rugged rock the ragged rascal ran",  # R, n, g clusters
    "Many men, many minds",  # M, n clusters
    "Lily ladles little Letty's lentil soup",  # L, t clusters
    "Nine nice night nurses nursing nicely",  # N, s clusters
    
    # Fricatives and affricates
    "She should sell her seashells",  # Sh, s, h sounds
    "The zoo's zebra zigzagged zealously",  # Z, z clusters
    "Which witch is which?",  # Wh, ch, ch sounds
    "The judge's job is just",  # J, dg, st clusters
    
    # Plosives and stops
    "Big black bug bit a big black bear",  # B, bl, g, t clusters
    "A proper copper coffee pot",  # P, c, f clusters
    "Double bubble gum bubbles double",  # D, bl, g, b clusters
    "Top cop",  # T, p, c clusters
    
    # Complex multi-syllable words
    "The anthropologist analyzed the archaeological artifacts",  # Complex consonant clusters
    "The psychologist's psychological assessment",  # Ps, ch, g clusters
    "Extraordinary extraterrestrial exploration",  # X, tr, str clusters
    "The mathematician's mathematical methodology",  # Th, m, th clusters
    
    # Stress patterns and rhythm
    "I scream, you scream, we all scream for ice cream",  # Varied stress
    "How much wood would a woodchuck chuck",  # W, ch, ck clusters
    "Betty Botter bought some butter",  # B, t, r clusters
    "A tutor who tooted a flute tried to tutor two tooters to toot",  # T, r, f clusters
    
    # Numbers and sequences (different phonemes)
    "One, two, three, four, five",  # W, th, f, v sounds
    "Seven, eight, nine, ten",  # S, v, n, t, n sounds
    "First, second, third, fourth, fifth",  # F, s, th, f, th clusters
    
    # Common authentication phrases
    "My voice is my password, verify me",  # V, s, p, f, m sounds
    "Authentication code one two three four",  # Th, c, d, f sounds
    "Please repeat after me",  # P, s, r, p, t, f, t, m sounds
    "Say your name and date of birth",  # S, n, d, t, b, th sounds
    
    # Financial/transaction phrases
    "I authorize this transaction for one thousand dollars",  # Th, z, s, tr, f, th, d sounds
    "My account number is four two seven nine",  # M, c, n, f, t, s, n sounds
    "Transfer funds to account ending in five six seven eight",  # Tr, f, n, c, n, d, f, s, v, t sounds
    
    # Emotional and prosodic variation
    "Oh my goodness, that's incredible!",  # O, m, g, n, th, t, s, n, cr, d sounds
    "Absolutely fantastic!",  # B, s, l, t, f, n, t, st sounds
    "What a wonderful surprise!",  # Wh, t, w, n, d, f, l, s, pr, z sounds
    
    # Tongue twisters (maximize difficulty)
    "Fuzzy Wuzzy was a bear, Fuzzy Wuzzy had no hair",  # F, z, w, z, b, h, d, n, h sounds
    "I saw a saw that could out saw any other saw I ever saw",  # S, w, s, th, t, c, d, t, s, n, th, r, s, v, r, s sounds
    "Can you can a can as a canner can can a can?",  # C, n, c, n, c, n, r, c, n, c, n, c, n sounds
]

# Extended set for maximum coverage
EXTENDED_PHRASES = [
    # Additional diphthongs
    "The boy pointed to the toy",  # oy, oi
    "I found a round pound on the ground",  # ou, ow, ou
    "The deer appeared near here",  # ea, ea, ea, ea
    "The bear stared at the pear",  # ea, ai, ea
    
    # Additional consonant clusters
    "The spring brings string things",  # spr, br, str, th
    "The screen screams",  # scr, cr
    "Splash and splurge",  # spl, spl
    "The strong string strung",  # str, str, str
    
    # Voiced/unvoiced pairs
    "Pat the bat",  # p/b
    "The cat sat on the mat",  # c/k, s, t, m
    "The goat wore a coat",  # g, t, w, r, c, t
    "The fan ran",  # f, n, r, n
    
    # Minimal pairs for contrast
    "Ship and sheep",  # sh, p, sh, p
    "Bit and beat",  # b, t, b, t
    "Cat and cut",  # c, t, c, t
    "Hat and hot",  # h, t, h, t
]


def get_phonetic_coverage(phrases: List[str]) -> Dict[str, any]:
    """
    Analyze phonetic coverage of phrases.
    Returns a dictionary with coverage statistics.
    """
    # Simplified phonetic analysis - in production, use phonemizer or espeak-ng
    all_text = " ".join(phrases).lower()
    
    # Count unique characters (rough proxy for phoneme diversity)
    unique_chars = set(all_text.replace(" ", "").replace(",", "").replace(".", "").replace("!", "").replace("?", ""))
    
    # Count consonant clusters (simplified)
    consonant_clusters = []
    for phrase in phrases:
        words = phrase.lower().split()
        for word in words:
            # Simple cluster detection (2+ consecutive consonants)
            for i in range(len(word) - 1):
                if word[i].isalpha() and word[i+1].isalpha():
                    if word[i] not in 'aeiou' and word[i+1] not in 'aeiou':
                        cluster = word[i:i+2]
                        if cluster not in consonant_clusters:
                            consonant_clusters.append(cluster)
    
    return {
        "total_phrases": len(phrases),
        "total_characters": len(all_text),
        "unique_characters": len(unique_chars),
        "consonant_clusters_found": len(consonant_clusters),
        "sample_clusters": consonant_clusters[:20],  # First 20 as sample
    }


def generate_elevenlabs(text: str, filename: str, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> bool:
    """Generate audio using ElevenLabs API."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not set. Skipping.")
        return False
        
    try:
        import requests
    except ImportError:
        logger.error("'requests' module not found. Please install it: pip install requests")
        logger.error("Or activate the virtual environment: source backend/venv/bin/activate")
        return False
    
    try:
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
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
        else:
            logger.error(f"ElevenLabs Error ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"ElevenLabs Exception: {e}")
        return False


def generate_openai(text: str, filename: str, voice: str = "alloy") -> bool:
    """Generate audio using OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set. Skipping.")
        return False
        
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("'openai' module not found. Please install it: pip install openai")
        logger.error("Or activate the virtual environment: source backend/venv/bin/activate")
        return False
        client = OpenAI(api_key=api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        response.stream_to_file(filename)
        return True
            
    except Exception as e:
        logger.error(f"OpenAI Exception: {e}")
        return False


def save_metadata(filename: Path, phrase: str, service: str, coverage_info: Dict) -> None:
    """Save metadata JSON for the generated sample."""
    metadata = {
        "phrase": phrase,
        "service": service,
        "timestamp": int(time.time()),
        "phonetic_coverage": {
            "phrase_length": len(phrase),
            "word_count": len(phrase.split()),
            "unique_chars": len(set(phrase.lower().replace(" ", "").replace(",", "").replace(".", "").replace("!", "").replace("?", ""))),
        },
        "generation_info": {
            "total_phrases_in_set": coverage_info.get("total_phrases", 0),
            "total_characters_in_set": coverage_info.get("total_characters", 0),
        }
    }
    
    metadata_path = filename.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Generate phonetically diverse voice samples for deepfake detection training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 50 samples using ElevenLabs
  python3 generate_phonetic_samples.py --service elevenlabs --count 50
  
  # Generate samples with extended phrase set
  python3 generate_phonetic_samples.py --service all --count 100 --extended
  
  # Custom output directory
  python3 generate_phonetic_samples.py --service openai --count 25 --output-dir data/phonetic_samples
        """
    )
    parser.add_argument(
        "--service",
        choices=["elevenlabs", "openai", "all"],
        default="all",
        help="TTS service to use (default: all)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of samples to generate per service (default: 50)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backend/data/library/phonetic",
        help="Output directory for generated samples (default: backend/data/library/phonetic)"
    )
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Use extended phrase set for maximum coverage"
    )
    parser.add_argument(
        "--voice-id",
        type=str,
        default="pNInz6obpgDQGcFmaJgB",
        help="ElevenLabs voice ID (default: Adam)"
    )
    parser.add_argument(
        "--openai-voice",
        type=str,
        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        default="alloy",
        help="OpenAI voice (default: alloy)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate generation without API calls"
    )
    
    args = parser.parse_args()
    
    # Check dependencies at startup (after logging is configured)
    deps_available = check_dependencies()
    if not deps_available and not args.dry_run:
        logger.warning("Continuing despite missing dependencies (will fail on API calls)")
    
    # Select phrase set
    phrases = PHONETIC_PHRASES + (EXTENDED_PHRASES if args.extended else [])
    
    # Analyze coverage
    coverage_info = get_phonetic_coverage(phrases)
    logger.info(f"Phonetic Coverage Analysis:")
    logger.info(f"  Total phrases: {coverage_info['total_phrases']}")
    logger.info(f"  Unique characters: {coverage_info['unique_characters']}")
    logger.info(f"  Consonant clusters found: {coverage_info['consonant_clusters_found']}")
    logger.info(f"  Sample clusters: {', '.join(coverage_info['sample_clusters'][:10])}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Determine services
    services = []
    if args.service == "all":
        services = ["elevenlabs", "openai"]
    else:
        services = [args.service]
    
    if args.dry_run:
        logger.info("DRY RUN: No actual API calls will be made.")
        logger.info(f"Would generate {args.count} samples per service: {', '.join(services)}")
        logger.info(f"Total samples: {args.count * len(services)}")
        return
    
    # Generate samples
    import random
    total_generated = 0
    total_failed = 0
    
    for service in services:
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating {args.count} samples using {service.upper()}")
        logger.info(f"{'='*60}")
        
        # Shuffle phrases for variety
        selected_phrases = random.sample(phrases, min(args.count, len(phrases)))
        
        for i, phrase in enumerate(selected_phrases, 1):
            timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
            filename = output_dir / f"{service}_phonetic_{timestamp}_{i}.mp3"
            
            logger.info(f"[{i}/{args.count}] Generating: '{phrase[:50]}{'...' if len(phrase) > 50 else ''}'")
            logger.info(f"  -> {filename.name}")
            
            success = False
            if service == "elevenlabs":
                success = generate_elevenlabs(phrase, str(filename), args.voice_id)
            elif service == "openai":
                success = generate_openai(phrase, str(filename), args.openai_voice)
            
            if success:
                # Save metadata
                save_metadata(filename, phrase, service, coverage_info)
                total_generated += 1
                logger.info("  ✓ Success")
                
                # Respect rate limits
                time.sleep(1.5)  # Slightly longer delay for API courtesy
            else:
                total_failed += 1
                logger.warning("  ✗ Failed")
                # Remove failed file if it exists
                if filename.exists():
                    filename.unlink()
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("Generation Summary")
    logger.info(f"{'='*60}")
    logger.info(f"Total generated: {total_generated}")
    logger.info(f"Total failed: {total_failed}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"\nMetadata files (.json) saved alongside audio files.")


if __name__ == "__main__":
    main()

