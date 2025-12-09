"""
Hugging Face deepfake detection sensor.

Uses Hugging Face Inference API to detect deepfakes using state-of-the-art models.
Implements retry/backoff for API reliability and fail-open behavior for robustness.
"""

import asyncio
import logging
import os
import io

import numpy as np
import scipy.io.wavfile

from .base import BaseSensor, SensorResult

# Optional dependency - import conditionally
try:
    from huggingface_hub import InferenceClient
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False
    InferenceClient = None

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0


class HFDeepfakeSensor(BaseSensor):
    """
    Uses Hugging Face Inference API to detect deepfakes using state-of-the-art models.
    Requires HUGGINGFACE_TOKEN in environment variables.

    Features:
    - Async/await pattern for non-blocking I/O in FastAPI
    - Retry with exponential backoff for transient API failures
    - Fail-open behavior: returns passed=True on errors to avoid false positives
    - Supports configurable model via HF_MODEL_ID environment variable
    - Optional SSL verification control via HF_SSL_VERIFY for Docker/corporate proxies
    """

    DEFAULT_MODEL_ID = "MelodyMachine/Deepfake-audio-detection-V2"

    def __init__(self):
        super().__init__("AI Deepfake Model (Hugging Face)")
        
        # Check if huggingface_hub is available
        if not HAS_HUGGINGFACE:
            logger.warning(
                "huggingface_hub library not installed. HFDeepfakeSensor will be disabled. "
                "Install it with: pip install huggingface_hub"
            )
            self.token = None
            self.model_id = None
            self.ssl_verify = True
            self.client = None
            return
        
        self.token = os.getenv("HUGGINGFACE_TOKEN")
        self.model_id = os.getenv("HF_MODEL_ID", self.DEFAULT_MODEL_ID)

        # SSL verification control for Docker/testing environments
        # Set HF_SSL_VERIFY=false to disable SSL verification (not recommended for production)
        ssl_verify = os.getenv("HF_SSL_VERIFY", "true").lower()
        self.ssl_verify = ssl_verify not in ("false", "0", "no")

        # Log startup warning if token is not set
        if not self.token:
            logger.warning(
                "HUGGINGFACE_TOKEN not set. HFDeepfakeSensor will skip API calls. "
                "Set this environment variable to enable Hugging Face deepfake detection."
            )

        if not self.ssl_verify:
            logger.warning(
                "SSL verification disabled for Hugging Face API (HF_SSL_VERIFY=false). "
                "This is insecure and should only be used for testing/development."
            )

        # Only create the client when token is available to avoid unnecessary API issues
        # Note: InferenceClient doesn't directly support ssl_verify parameter
        # SSL configuration is handled at the requests/httpx library level
        self.client = InferenceClient(token=self.token) if self.token else None

    async def _call_api_with_retry(self, audio_bytes: bytes) -> list:
        """
        Call Hugging Face API with exponential backoff retry logic.

        Uses asyncio.sleep() instead of time.sleep() to avoid blocking the event loop
        in async FastAPI applications.

        Args:
            audio_bytes: WAV audio data as bytes

        Returns:
            List of classification results from the API

        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(MAX_RETRIES):
            try:
                # Run the blocking API call in a thread pool to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.audio_classification(
                        model=self.model_id,
                        data=audio_bytes
                    )
                )
                return response
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"HF API call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                        f"Retrying in {backoff:.1f}s..."
                    )
                    # Use asyncio.sleep instead of time.sleep to avoid blocking event loop
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER

        raise last_exception

    async def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        """
        Analyze audio for deepfake detection using Hugging Face API.

        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz

        Returns:
            SensorResult with deepfake detection findings
        """
        if not HAS_HUGGINGFACE:
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=0.0,
                detail="Skipped: huggingface_hub library not installed",
                threshold=0.5
            )
        
        if not self.token:
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=0.0,
                detail="Skipped: HUGGINGFACE_TOKEN not set",
                threshold=0.5
            )

        # Validate input
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=True,  # Fail open
                value=0.0,
                detail="Invalid or empty audio input",
                threshold=0.5
            )

        # Convert numpy audio to 16-bit PCM for API transmission
        # Handle different audio data types with proper scaling
        if np.issubdtype(audio_data.dtype, np.floating):
            # Float audio: clip to [-1, 1] range to prevent int16 overflow
            clipped_audio = np.clip(audio_data, -1.0, 1.0)
            audio_pcm = (clipped_audio * 32767).astype(np.int16)
        elif np.issubdtype(audio_data.dtype, np.signedinteger):
            # Integer audio: scale to int16 range if needed
            if audio_data.dtype == np.int16:
                # Already int16, no conversion needed
                audio_pcm = audio_data
            elif audio_data.dtype in (np.int32, np.int64):
                # Scale down from int32/int64 to int16 range
                # Determine the scale factor based on actual data type
                max_val = np.iinfo(audio_data.dtype).max
                scaled = (audio_data.astype(np.float64) / max_val * 32767)
                audio_pcm = scaled.astype(np.int16)
            else:
                # int8 or other small integer types: scale up to int16
                max_val = np.iinfo(audio_data.dtype).max
                scaled = (audio_data.astype(np.float64) / max_val * 32767)
                audio_pcm = scaled.astype(np.int16)
        else:
            # Fallback for unknown types: convert to float then to int16
            logger.warning(f"Unexpected audio dtype {audio_data.dtype}, converting via float")
            clipped_audio = np.clip(audio_data.astype(np.float64), -1.0, 1.0)
            audio_pcm = (clipped_audio * 32767).astype(np.int16)

        # Use context manager to ensure BytesIO is properly closed
        with io.BytesIO() as byte_io:
            scipy.io.wavfile.write(byte_io, samplerate, audio_pcm)
            audio_bytes = byte_io.getvalue()

        try:
            # The API returns a list of dicts: [{'label': 'real', 'score': 0.99}, ...]
            # Await the async API call
            response = await self._call_api_with_retry(audio_bytes)

            # Parse response (model specific labels: usually 'fake'/'real' or 'bonafide'/'spoof')
            fake_score = 0.0
            label_map = {
                "fake": 1.0, "spoof": 1.0, "synthetic": 1.0,
                "real": 0.0, "bonafide": 0.0, "genuine": 0.0
            }

            top_result = max(response, key=lambda x: x['score'])
            predicted_label = top_result['label'].lower()

            # Map label to a 0-1 synthetic score
            if predicted_label in label_map:
                if label_map[predicted_label] == 1.0:
                    fake_score = top_result['score']
                else:
                    fake_score = 1.0 - top_result['score']
            else:
                # Fallback if labels are unexpected
                fake_score = 0.5

            is_synthetic = fake_score > 0.5

            # Explicitly convert to Python float to ensure proper numpy type handling
            fake_score_float = float(fake_score)

            return SensorResult(
                sensor_name=self.name,
                passed=not is_synthetic,
                value=float(round(fake_score_float, 3)),
                threshold=0.5,
                detail=f"Model confidence: {top_result['score']:.1%} ({top_result['label']})"
            )

        except Exception as e:
            logger.error(f"HFDeepfakeSensor API error after {MAX_RETRIES} retries: {e}")
            return SensorResult(
                sensor_name=self.name,
                passed=True,  # Fail open on API error
                value=0.0,
                detail=f"API Error: {str(e)}",
                threshold=0.5
            )
