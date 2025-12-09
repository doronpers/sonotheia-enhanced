"""
Hugging Face Ensemble Deepfake Detection Sensor.

Provides advanced HF integration with:
- Multiple model support for ensemble detection
- Rate limiting awareness with queue management
- Model warm-up for reduced cold-start latency
- Batch processing support
- Local model fallback when API is unavailable
"""

import asyncio
import logging
import os
import io
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

import numpy as np
import scipy.io.wavfile

from .base import BaseSensor, SensorResult

logger = logging.getLogger(__name__)

# Retry and rate limit configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0
RATE_LIMIT_WINDOW_SECONDS = 60.0
DEFAULT_RATE_LIMIT_PER_MINUTE = 60


class ModelStatus(Enum):
    """Status of a model in the ensemble."""
    READY = "ready"
    WARMING_UP = "warming_up"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class ModelConfig:
    """Configuration for a single HF model."""
    model_id: str
    weight: float = 1.0  # Weight in ensemble voting
    enabled: bool = True
    label_mapping: Optional[Dict[str, float]] = None  # Maps labels to fake scores
    
    def __post_init__(self):
        if self.label_mapping is None:
            # Default mapping: fake/spoof/synthetic -> 1.0, real/bonafide/genuine -> 0.0
            self.label_mapping = {
                "fake": 1.0, "spoof": 1.0, "synthetic": 1.0,
                "real": 0.0, "bonafide": 0.0, "genuine": 0.0
            }


@dataclass
class RateLimitState:
    """Tracks rate limit state for a model."""
    request_times: deque = field(default_factory=lambda: deque(maxlen=100))
    rate_limited_until: Optional[float] = None
    requests_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limit."""
        now = time.time()
        
        # Check if we're in a rate limit cooldown
        if self.rate_limited_until and now < self.rate_limited_until:
            return False
        
        # Clean old requests outside the window
        window_start = now - RATE_LIMIT_WINDOW_SECONDS
        while self.request_times and self.request_times[0] < window_start:
            self.request_times.popleft()
        
        return len(self.request_times) < self.requests_per_minute
    
    def record_request(self):
        """Record a request timestamp."""
        self.request_times.append(time.time())
    
    def set_rate_limited(self, cooldown_seconds: float = 60.0):
        """Set rate limit cooldown."""
        self.rate_limited_until = time.time() + cooldown_seconds


@dataclass
class ModelResult:
    """Result from a single model in the ensemble."""
    model_id: str
    fake_score: float
    confidence: float
    label: str
    weight: float
    status: ModelStatus
    error: Optional[str] = None
    latency_ms: Optional[float] = None


# Default models for ensemble detection
DEFAULT_MODELS = [
    ModelConfig(
        model_id="MelodyMachine/Deepfake-audio-detection-V2",
        weight=1.0,
    ),
]


class HFEnsembleSensor(BaseSensor):
    """
    Ensemble sensor that runs multiple HF deepfake detection models in parallel.
    
    Features:
    - Multiple model support with weighted voting
    - Rate limiting awareness with queue management
    - Model warm-up on startup
    - Batch processing support
    - Local model fallback when API is unavailable
    
    Environment Variables:
    - HUGGINGFACE_TOKEN: API token for HF Inference API
    - HF_ENSEMBLE_MODELS: Comma-separated list of model IDs
    - HF_LOCAL_FALLBACK: Enable local model fallback (true/false)
    - HF_WARMUP_ENABLED: Enable model warm-up on init (true/false)
    """
    
    def __init__(
        self,
        models: Optional[List[ModelConfig]] = None,
        enable_warmup: bool = True,
        enable_local_fallback: bool = True,
        category: str = "prosecution"
    ):
        super().__init__("AI Deepfake Ensemble (Hugging Face)", category=category)
        self.token = os.getenv("HUGGINGFACE_TOKEN")
        
        # Parse models from environment or use defaults
        self.models = models or self._load_models_from_env()
        
        # Local fallback settings
        env_local_fallback = os.getenv("HF_LOCAL_FALLBACK", "true").lower()
        self.enable_local_fallback = enable_local_fallback and env_local_fallback in ("true", "1", "yes")
        
        # Warm-up settings
        env_warmup = os.getenv("HF_WARMUP_ENABLED", "true").lower()
        self.enable_warmup = enable_warmup and env_warmup in ("true", "1", "yes")
        
        # Model states
        self.model_states: Dict[str, ModelStatus] = {}
        self.rate_limit_states: Dict[str, RateLimitState] = {}
        self._initialized = False
        
        # Local model cache (lazy loaded)
        self._local_pipeline = None
        self._local_model_available = False
        
        # HF client (lazy loaded)
        self._client = None
        
        # Request queue for rate limit management
        self._request_queue: deque = deque()
        self._queue_lock = asyncio.Lock()
        
        # Log startup info (avoid logging full model IDs in production)
        model_count = len([m for m in self.models if m.enabled])
        logger.info(f"HFEnsembleSensor initialized with {model_count} model(s)")
        
        if not self.token:
            logger.warning(
                "HUGGINGFACE_TOKEN not set. API calls will be skipped. "
                "Local fallback will be used if enabled."
            )
    
    def _load_models_from_env(self) -> List[ModelConfig]:
        """Load model configurations from environment variables."""
        env_models = os.getenv("HF_ENSEMBLE_MODELS", "")
        if not env_models:
            return DEFAULT_MODELS.copy()
        
        model_ids = [m.strip() for m in env_models.split(",") if m.strip()]
        return [ModelConfig(model_id=mid) for mid in model_ids]
    
    @property
    def client(self):
        """Lazy-load HF InferenceClient."""
        if self._client is None and self.token:
            try:
                from huggingface_hub import InferenceClient
                self._client = InferenceClient(token=self.token)
            except ImportError:
                logger.error("huggingface_hub not installed")
        return self._client
    
    async def initialize(self):
        """Initialize sensor, optionally warm up models."""
        if self._initialized:
            return
        
        # Initialize model states
        for model in self.models:
            if model.enabled:
                self.model_states[model.model_id] = ModelStatus.READY
                self.rate_limit_states[model.model_id] = RateLimitState()
        
        # Warm up models if enabled
        if self.enable_warmup and self.token:
            await self._warmup_models()
        
        # Check local fallback availability
        if self.enable_local_fallback:
            self._check_local_model_availability()
        
        self._initialized = True
    
    async def _warmup_models(self):
        """Warm up models by sending a small test request."""
        logger.info("Starting model warm-up...")
        
        # Generate a short test audio (100ms of silence)
        test_audio = np.zeros(1600, dtype=np.float32)  # 100ms at 16kHz
        
        for model in self.models:
            if not model.enabled:
                continue
            
            self.model_states[model.model_id] = ModelStatus.WARMING_UP
            try:
                # Create minimal audio bytes
                audio_pcm = (test_audio * 32767).astype(np.int16)
                with io.BytesIO() as byte_io:
                    scipy.io.wavfile.write(byte_io, 16000, audio_pcm)
                    audio_bytes = byte_io.getvalue()
                
                # Try a request
                await self._call_model_api(model.model_id, audio_bytes, timeout=10.0)
                self.model_states[model.model_id] = ModelStatus.READY
                logger.info(f"Model {model.model_id} warmed up successfully")
            except Exception as e:
                logger.warning(f"Model {model.model_id} warm-up failed: {e}")
                self.model_states[model.model_id] = ModelStatus.READY  # Still ready for requests
    
    def _check_local_model_availability(self):
        """Check if local transformers model is available."""
        try:
            import torch
            from transformers import pipeline
            self._local_model_available = True
            logger.info("Local transformers fallback available")
        except ImportError:
            self._local_model_available = False
            logger.info("Local transformers fallback not available (transformers/torch not installed)")
    
    def _load_local_pipeline(self):
        """Lazy load the local transformers pipeline."""
        if self._local_pipeline is not None:
            return self._local_pipeline
        
        if not self._local_model_available:
            return None
        
        try:
            from transformers import pipeline
            import torch
            
            # Use a lightweight model for local inference
            # This model should be cached after first download
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._local_pipeline = pipeline(
                "audio-classification",
                model="MelodyMachine/Deepfake-audio-detection-V2",
                device=device,
            )
            logger.info(f"Local pipeline loaded on {device}")
            return self._local_pipeline
        except Exception as e:
            logger.error(f"Failed to load local pipeline: {e}")
            self._local_model_available = False
            return None
    
    async def _call_model_api(
        self,
        model_id: str,
        audio_bytes: bytes,
        timeout: float = 30.0
    ) -> List[Dict[str, Any]]:
        """Call HF API for a single model with rate limiting awareness."""
        if not self.client:
            raise RuntimeError("HF client not available")
        
        # Check rate limit
        rate_state = self.rate_limit_states.get(model_id)
        if rate_state and not rate_state.can_make_request():
            raise RuntimeError(f"Rate limited for model {model_id}")
        
        # Record request
        if rate_state:
            rate_state.record_request()
        
        # Run the blocking API call in a thread pool
        loop = asyncio.get_event_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.audio_classification(
                        model=model_id,
                        data=audio_bytes
                    )
                ),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout calling model {model_id}")
        except Exception as e:
            # Check for rate limit error
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                if rate_state:
                    rate_state.set_rate_limited(60.0)
                self.model_states[model_id] = ModelStatus.RATE_LIMITED
            raise
    
    async def _call_model_with_retry(
        self,
        model_config: ModelConfig,
        audio_bytes: bytes
    ) -> ModelResult:
        """Call a single model with exponential backoff retry."""
        start_time = time.time()
        last_exception = None
        backoff = INITIAL_BACKOFF_SECONDS
        
        for attempt in range(MAX_RETRIES):
            try:
                response = await self._call_model_api(model_config.model_id, audio_bytes)
                
                # Parse response
                fake_score, confidence, label = self._parse_response(
                    response, model_config.label_mapping
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                return ModelResult(
                    model_id=model_config.model_id,
                    fake_score=fake_score,
                    confidence=confidence,
                    label=label,
                    weight=model_config.weight,
                    status=ModelStatus.READY,
                    latency_ms=latency_ms
                )
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Model {model_config.model_id} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {backoff:.1f}s..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
        
        latency_ms = (time.time() - start_time) * 1000
        return ModelResult(
            model_id=model_config.model_id,
            fake_score=0.0,
            confidence=0.0,
            label="error",
            weight=model_config.weight,
            status=ModelStatus.ERROR,
            error=str(last_exception),
            latency_ms=latency_ms
        )
    
    def _parse_response(
        self,
        response: List[Dict[str, Any]],
        label_mapping: Dict[str, float]
    ) -> Tuple[float, float, str]:
        """Parse HF API response to extract fake score."""
        if not response:
            return 0.5, 0.0, "unknown"
        
        top_result = max(response, key=lambda x: x.get('score', 0))
        label = top_result.get('label', '').lower()
        confidence = top_result.get('score', 0.0)
        
        if label in label_mapping:
            if label_mapping[label] == 1.0:
                fake_score = confidence
            else:
                fake_score = 1.0 - confidence
        else:
            fake_score = 0.5
        
        return fake_score, confidence, top_result.get('label', 'unknown')
    
    async def _call_local_fallback(
        self,
        audio_data: np.ndarray,
        samplerate: int
    ) -> ModelResult:
        """Use local transformers model as fallback."""
        pipeline = self._load_local_pipeline()
        if pipeline is None:
            return ModelResult(
                model_id="local_fallback",
                fake_score=0.0,
                confidence=0.0,
                label="unavailable",
                weight=1.0,
                status=ModelStatus.UNAVAILABLE,
                error="Local pipeline not available"
            )
        
        start_time = time.time()
        
        try:
            # Prepare audio for local pipeline
            # Resample if needed (pipeline expects 16kHz)
            if samplerate != 16000:
                from scipy import signal
                samples = int(len(audio_data) * 16000 / samplerate)
                audio_data = signal.resample(audio_data, samples)
                samplerate = 16000
            
            # Save to temp bytes for pipeline
            audio_pcm = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
            with io.BytesIO() as byte_io:
                scipy.io.wavfile.write(byte_io, samplerate, audio_pcm)
                audio_bytes = byte_io.getvalue()
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: pipeline(audio_bytes))
            
            # Parse result
            fake_score, confidence, label = self._parse_response(
                result,
                {"fake": 1.0, "real": 0.0, "spoof": 1.0, "bonafide": 0.0}
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ModelResult(
                model_id="local_fallback",
                fake_score=fake_score,
                confidence=confidence,
                label=label,
                weight=1.0,
                status=ModelStatus.READY,
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Local fallback failed: {e}")
            return ModelResult(
                model_id="local_fallback",
                fake_score=0.0,
                confidence=0.0,
                label="error",
                weight=1.0,
                status=ModelStatus.ERROR,
                error=str(e),
                latency_ms=latency_ms
            )
    
    def _prepare_audio_bytes(
        self,
        audio_data: np.ndarray,
        samplerate: int
    ) -> bytes:
        """Convert audio data to WAV bytes for API transmission."""
        # Handle different audio data types with proper scaling
        if np.issubdtype(audio_data.dtype, np.floating):
            clipped_audio = np.clip(audio_data, -1.0, 1.0)
            audio_pcm = (clipped_audio * 32767).astype(np.int16)
        elif np.issubdtype(audio_data.dtype, np.signedinteger):
            if audio_data.dtype == np.int16:
                audio_pcm = audio_data
            else:
                max_val = np.iinfo(audio_data.dtype).max
                scaled = (audio_data.astype(np.float64) / max_val * 32767)
                audio_pcm = scaled.astype(np.int16)
        else:
            clipped_audio = np.clip(audio_data.astype(np.float64), -1.0, 1.0)
            audio_pcm = (clipped_audio * 32767).astype(np.int16)
        
        with io.BytesIO() as byte_io:
            scipy.io.wavfile.write(byte_io, samplerate, audio_pcm)
            return byte_io.getvalue()
    
    def _aggregate_results(self, results: List[ModelResult]) -> Tuple[float, bool, str]:
        """Aggregate ensemble results using weighted voting."""
        # Filter out failed results
        valid_results = [r for r in results if r.status == ModelStatus.READY]
        
        if not valid_results:
            # All models failed - check if we have any results at all
            if results:
                errors = [r.error for r in results if r.error]
                return 0.0, True, f"All models failed: {'; '.join(errors[:3])}"
            return 0.0, True, "No models available"
        
        # Weighted average of fake scores
        total_weight = sum(r.weight for r in valid_results)
        weighted_score = sum(r.fake_score * r.weight for r in valid_results) / total_weight
        
        # Determine if synthetic (threshold 0.5)
        is_synthetic = weighted_score > 0.5
        
        # Build detail message
        model_details = ", ".join(
            f"{r.model_id.split('/')[-1]}:{r.fake_score:.2f}"
            for r in valid_results
        )
        detail = f"Ensemble score: {weighted_score:.2%} ({model_details})"
        
        return weighted_score, not is_synthetic, detail
    
    async def analyze(
        self,
        audio_data: np.ndarray,
        samplerate: int
    ) -> SensorResult:
        """
        Analyze audio for deepfake detection using ensemble of HF models.
        
        Args:
            audio_data: Audio signal as numpy array
            samplerate: Sample rate in Hz
            
        Returns:
            SensorResult with deepfake detection findings
        """
        # Ensure initialized
        if not self._initialized:
            await self.initialize()
        
        # Validate input
        if not self.validate_input(audio_data, samplerate):
            return SensorResult(
                sensor_name=self.name,
                passed=True,  # Fail open
                value=0.0,
                detail="Invalid or empty audio input",
                threshold=0.5
            )
        
        # Check if we have any available models
        enabled_models = [m for m in self.models if m.enabled]
        if not enabled_models and not self.enable_local_fallback:
            return SensorResult(
                sensor_name=self.name,
                passed=True,
                value=0.0,
                detail="No models configured",
                threshold=0.5
            )
        
        # Prepare audio bytes
        audio_bytes = self._prepare_audio_bytes(audio_data, samplerate)
        
        # Run models in parallel if we have API access
        results: List[ModelResult] = []
        
        if self.token and enabled_models:
            # Create tasks for all enabled models
            tasks = [
                self._call_model_with_retry(model, audio_bytes)
                for model in enabled_models
            ]
            
            # Run all models in parallel
            results = await asyncio.gather(*tasks)
        
        # Check if all API models failed and we should use local fallback
        api_success = any(r.status == ModelStatus.READY for r in results)
        
        if not api_success and self.enable_local_fallback and self._local_model_available:
            logger.info("API models unavailable, using local fallback")
            local_result = await self._call_local_fallback(audio_data, samplerate)
            results.append(local_result)
        
        # Handle case where no API and no local fallback
        if not results:
            return SensorResult(
                sensor_name=self.name,
                passed=True,  # Fail open
                value=0.0,
                detail="Skipped: HUGGINGFACE_TOKEN not set and no local fallback",
                threshold=0.5
            )
        
        # Aggregate results
        weighted_score, passed, detail = self._aggregate_results(results)
        
        # Build metadata with individual model results
        metadata = {
            "models_used": len([r for r in results if r.status == ModelStatus.READY]),
            "models_failed": len([r for r in results if r.status != ModelStatus.READY]),
            "model_results": [
                {
                    "model_id": r.model_id,
                    "fake_score": round(r.fake_score, 3),
                    "confidence": round(r.confidence, 3),
                    "label": r.label,
                    "status": r.status.value,
                    "latency_ms": round(r.latency_ms, 1) if r.latency_ms else None,
                }
                for r in results
            ],
        }
        
        return SensorResult(
            sensor_name=self.name,
            passed=passed,
            value=float(round(weighted_score, 3)),
            threshold=0.5,
            detail=detail,
            metadata=metadata
        )
    
    async def analyze_batch(
        self,
        audio_items: List[Tuple[np.ndarray, int]],
        max_concurrent: int = 5
    ) -> List[SensorResult]:
        """
        Analyze multiple audio files in batch for efficiency.
        
        Args:
            audio_items: List of (audio_data, samplerate) tuples
            max_concurrent: Maximum concurrent analysis tasks
            
        Returns:
            List of SensorResults in same order as input
        """
        if not self._initialized:
            await self.initialize()
        
        # Use semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(audio_data: np.ndarray, samplerate: int) -> SensorResult:
            async with semaphore:
                return await self.analyze(audio_data, samplerate)
        
        # Create tasks for all items
        tasks = [
            analyze_with_limit(audio_data, samplerate)
            for audio_data, samplerate in audio_items
        ]
        
        # Run all with controlled concurrency
        return await asyncio.gather(*tasks)
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current status of all models in the ensemble."""
        return {
            "models": [
                {
                    "model_id": model.model_id,
                    "enabled": model.enabled,
                    "weight": model.weight,
                    "status": self.model_states.get(model.model_id, ModelStatus.UNAVAILABLE).value,
                    "rate_limited": self._is_rate_limited(model.model_id),
                }
                for model in self.models
            ],
            "local_fallback_available": self._local_model_available,
            "api_available": bool(self.token),
        }
    
    def _is_rate_limited(self, model_id: str) -> bool:
        """Check if a model is currently rate limited."""
        rate_state = self.rate_limit_states.get(model_id)
        if rate_state is None:
            return False
        if rate_state.rate_limited_until is None:
            return False
        return time.time() < rate_state.rate_limited_until
    
    def list_available_models(self) -> List[str]:
        """List all available model IDs."""
        return [m.model_id for m in self.models if m.enabled]
    
    def add_model(self, model_id: str, weight: float = 1.0):
        """Add a new model to the ensemble at runtime."""
        if any(m.model_id == model_id for m in self.models):
            logger.warning(f"Model {model_id} already in ensemble")
            return
        
        config = ModelConfig(model_id=model_id, weight=weight)
        self.models.append(config)
        self.model_states[model_id] = ModelStatus.READY
        self.rate_limit_states[model_id] = RateLimitState()
        logger.info(f"Added model {model_id} to ensemble")
    
    def remove_model(self, model_id: str):
        """Remove a model from the ensemble at runtime."""
        self.models = [m for m in self.models if m.model_id != model_id]
        self.model_states.pop(model_id, None)
        self.rate_limit_states.pop(model_id, None)
        logger.info(f"Removed model {model_id} from ensemble")
