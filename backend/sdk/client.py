import requests
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class SonotheiaClient:
    """
    Python Client SDK for Sonotheia Enhanced API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the Sonotheia API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})
            
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise errors if needed."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"API Request failed: {e}")
            try:
                error_detail = response.json()
                raise ValueError(f"API Error: {error_detail.get('detail', str(e))}")
            except json.JSONDecodeError:
                raise ValueError(f"API Error: {response.text}")
                
    def authenticate(self, 
                     transaction_id: str, 
                     customer_id: str, 
                     amount_usd: float, 
                     voice_sample: Optional[bytes] = None,
                     device_info: Optional[Dict] = None,
                     **kwargs) -> Dict[str, Any]:
        """
        Perform multi-factor authentication.
        
        Args:
            transaction_id: Unique transaction ID
            customer_id: Customer ID
            amount_usd: Transaction amount
            voice_sample: Optional voice audio bytes
            device_info: Optional device information dict
            **kwargs: Additional arguments for AuthenticationRequest
            
        Returns:
            Authentication response dict
        """
        payload = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "amount_usd": amount_usd,
            "voice_sample": list(voice_sample) if voice_sample else None, # Pydantic expects list for bytes sometimes, or base64
            "device_info": device_info,
            **kwargs
        }
        
        # Note: For large audio, we might need to handle base64 encoding or multipart upload
        # The current API expects JSON body with fields.
        
        url = f"{self.base_url}/api/authenticate"
        response = self.session.post(url, json=payload)
        return self._handle_response(response)

    def detect_voice(self, audio_file: Union[str, Path, bytes], quick_mode: bool = False) -> Dict[str, Any]:
        """
        Run deepfake detection on an audio file.
        
        Args:
            audio_file: Path to file or bytes
            quick_mode: Whether to run in quick mode
            
        Returns:
            Detection results
        """
        url = f"{self.base_url}/api/detect"
        params = {"quick_mode": quick_mode}
        
        files = {}
        if isinstance(audio_file, (str, Path)):
            files = {"file": open(audio_file, "rb")}
        else:
            files = {"file": ("audio.wav", audio_file, "audio/wav")}
            
        try:
            response = self.session.post(url, params=params, files=files)
            return self._handle_response(response)
        finally:
            if isinstance(audio_file, (str, Path)):
                files["file"].close()

    def generate_sar(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a Suspicious Activity Report.
        
        Args:
            context: SAR context dictionary
            
        Returns:
            Generated SAR narrative and validation
        """
        url = f"{self.base_url}/api/sar/generate"
        response = self.session.post(url, json=context)
        return self._handle_response(response)
        
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        url = f"{self.base_url}/api/v1/health"
        response = self.session.get(url)
        return self._handle_response(response)
