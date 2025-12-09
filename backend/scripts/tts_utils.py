#!/usr/bin/env python3
"""
TTS Utilities

Shared text-to-speech generation functions for ElevenLabs and OpenAI APIs.
Used by generate_phonetic_samples.py and generate_red_team.py.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def load_env_file(script_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from .env file.

    Args:
        script_path: Path to the calling script (used to find project root)

    Returns:
        True if .env was loaded successfully, False otherwise
    """
    try:
        from dotenv import load_dotenv

        if script_path:
            # Calculate project root from script location
            script_dir = Path(script_path).parent  # backend/scripts/
            project_root = script_dir.parent.parent  # project root
            env_path = project_root / ".env"
        else:
            # Use current working directory
            env_path = Path.cwd() / ".env"

        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            logger.debug(f"Loaded .env from: {env_path}")
            return True
        else:
            # Fallback: try current directory and parent directories
            load_dotenv(override=True)
            logger.debug("Attempted to load .env from current directory or parents")
            return True

    except ImportError:
        logger.debug("python-dotenv not installed, using system environment variables only")
        return False
    except Exception as e:
        logger.debug(f"Could not load .env: {e}")
        return False


def check_tts_dependencies() -> dict:
    """
    Check if required TTS dependencies are available.

    Returns:
        dict with 'requests' and 'openai' boolean availability
    """
    deps = {'requests': False, 'openai': False}

    try:
        import requests  # noqa: F401
        deps['requests'] = True
    except ImportError:
        pass

    try:
        from openai import OpenAI  # noqa: F401
        deps['openai'] = True
    except ImportError:
        pass

    return deps


def generate_elevenlabs(
    text: str,
    filename: str,
    voice_id: str = "pNInz6obpgDQGcFmaJgB",
    api_key: Optional[str] = None,
    timeout: int = 30
) -> bool:
    """
    Generate audio using ElevenLabs API.

    Args:
        text: Text to synthesize
        filename: Output file path
        voice_id: ElevenLabs voice ID (default: Adam)
        api_key: API key (uses env var if not provided)
        timeout: Request timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("ELEVENLABS_API_KEY not set. Skipping.")
        return False

    try:
        import requests
    except ImportError:
        logger.error("'requests' module not found. Please install it: pip install requests")
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

        response = requests.post(url, json=data, headers=headers, timeout=timeout)

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


def generate_openai(
    text: str,
    filename: str,
    voice: str = "alloy",
    api_key: Optional[str] = None
) -> bool:
    """
    Generate audio using OpenAI TTS API.

    Args:
        text: Text to synthesize
        filename: Output file path
        voice: OpenAI voice name (alloy, echo, fable, onyx, nova, shimmer)
        api_key: API key (uses env var if not provided)

    Returns:
        True if successful, False otherwise
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set. Skipping.")
        return False

    try:
        from openai import OpenAI
    except ImportError:
        logger.error("'openai' module not found. Please install it: pip install openai")
        return False

    try:
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
