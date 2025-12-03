import os
import requests
import logging
import asyncio
import numpy as np
from typing import Dict, Any, Optional

from backend.sensors.base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

class HuggingFaceDetectorSensor(BaseSensor):
    """
    Uses HuggingFace Inference API to detect deepfakes.
    Fails open (returns None) if API key is missing or API call fails.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = os.getenv("HF_TOKEN")
        self.api_url = self.config.get("api_url", "https://api-inference.huggingface.co/models/MelodyMachine/Deepfake-audio-detection")

    def analyze(self, audio_data: np.ndarray, samplerate: int) -> SensorResult:
        # This method is designed to be run in a thread pool by the registry
        # But we can also use asyncio directly if we were async.
        # Since the base class defines synchronous analyze, we'll keep it sync here
        # and let the registry handle the threading.
        
        if not self.api_key:
            logger.warning("HF_TOKEN not set, skipping HuggingFace detector")
            return SensorResult(
                sensor_name="HuggingFace Detector",
                passed=None, # Skipped
                value=0.0,
                threshold=0.0,
                reason="Skipped: HF_TOKEN missing",
                detail="API key not configured"
            )

        try:
            # Convert audio to bytes for upload (e.g. WAV)
            import io
            import soundfile as sf
            
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, samplerate, format='wav')
            buffer.seek(0)
            audio_bytes = buffer.read()
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=audio_bytes,
                timeout=5.0 # Short timeout to avoid blocking too long
            )
            
            if response.status_code != 200:
                logger.warning(f"HuggingFace API failed: {response.status_code} - {response.text}")
                return SensorResult(
                    sensor_name="HuggingFace Detector",
                    passed=None,
                    value=0.0,
                    threshold=0.0,
                    reason=f"API Error: {response.status_code}",
                    detail=response.text[:100]
                )
                
            # Parse response
            # Expected format: [{"label": "fake", "score": 0.9}, {"label": "real", "score": 0.1}]
            results = response.json()
            
            # Find score for 'fake' or 'spoof'
            fake_score = 0.0
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, list): # Sometimes it returns list of lists
                         for subitem in item:
                             if subitem.get("label", "").lower() in ["fake", "spoof", "synthetic"]:
                                 fake_score = subitem.get("score", 0.0)
                    elif item.get("label", "").lower() in ["fake", "spoof", "synthetic"]:
                        fake_score = item.get("score", 0.0)
            
            threshold = 0.5
            passed = fake_score < threshold
            
            return SensorResult(
                sensor_name="HuggingFace Detector",
                passed=passed,
                value=float(fake_score),
                threshold=threshold,
                reason="High probability of deepfake" if not passed else None,
                detail=f"Fake score: {fake_score:.3f}",
                metadata={"raw_response": str(results)[:200]}
            )
            
        except Exception as e:
            logger.error(f"HuggingFace detector failed: {e}")
            return SensorResult(
                sensor_name="HuggingFace Detector",
                passed=None,
                value=0.0,
                threshold=0.0,
                reason=f"Exception: {str(e)}",
                detail=None
            )
