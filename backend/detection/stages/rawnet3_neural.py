"""
Stage 4: RawNet3 Neural Network Detection

Deep learning-based detection using RawNet3 architecture.
"""

import logging
from typing import Dict, Any, Optional

import numpy as np

from ..models.rawnet3 import RawNet3Detector
from ..config import RawNet3Config

logger = logging.getLogger(__name__)


class RawNet3Stage:
    """
    Stage 4: RawNet3 Neural Network

    Uses deep learning for end-to-end audio deepfake detection.
    In demo mode, returns placeholder scores.
    """

    def __init__(
        self,
        config: Optional[RawNet3Config] = None,
        demo_mode: bool = True,
    ):
        """
        Initialize RawNet3 stage.

        Args:
            config: RawNet3 configuration
            demo_mode: Whether to use demo mode (placeholder scores)
        """
        self.config = config or RawNet3Config()
        self.demo_mode = demo_mode
        self.detector = None

        self._initialize_detector()
        logger.info(f"RawNet3Stage initialized: demo_mode={demo_mode}")

    def _initialize_detector(self) -> None:
        """Initialize the RawNet3 detector."""
        try:
            self.detector = RawNet3Detector(
                model_path=self.config.model_path,
                device=self.config.device,
                demo_mode=self.demo_mode,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize RawNet3 detector: {e}")
            self.detector = None

    def process(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Run RawNet3 detection on audio.

        Args:
            audio: Input audio array

        Returns:
            Dictionary containing detection results
        """
        if audio is None or len(audio) == 0:
            return self._empty_result("Empty audio input")

        if self.detector is None:
            return self._demo_result(audio)

        try:
            # Run detection
            result = self.detector.detect(audio)

            return {
                "success": True,
                "score": float(result.get("score", 0.5)),
                "confidence": float(result.get("confidence", 0.0)),
                "is_spoof": bool(result.get("is_spoof", False)),
                "demo_mode": result.get("demo_mode", self.demo_mode),
                "model_output": result,
            }

        except Exception as e:
            logger.error(f"RawNet3 detection failed: {e}")
            return self._empty_result(str(e))

    def _demo_result(self, audio: np.ndarray) -> Dict[str, Any]:
        """Generate demo mode result."""
        # Generate deterministic demo score
        if len(audio) > 0:
            audio_energy = np.sqrt(np.mean(audio ** 2))
            demo_score = 0.15 + 0.1 * min(audio_energy * 10, 1.0)
        else:
            demo_score = 0.5

        return {
            "success": True,
            "score": float(demo_score),
            "confidence": 0.85,
            "is_spoof": demo_score > 0.5,
            "demo_mode": True,
            "model_output": {
                "message": "DEMO MODE - placeholder score, not for production"
            },
        }

    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for failed detection."""
        return {
            "success": False,
            "error": error_msg,
            "score": 0.5,
            "confidence": 0.0,
            "is_spoof": False,
            "demo_mode": self.demo_mode,
            "model_output": {},
        }


class RawNet3BatchProcessor:
    """
    Batch processor for RawNet3 stage.

    Handles chunking for large audio files.
    """

    def __init__(
        self,
        stage: RawNet3Stage,
        chunk_size: int = 160000,  # 10 seconds at 16kHz
        overlap: int = 16000,  # 1 second overlap
    ):
        """
        Initialize batch processor.

        Args:
            stage: RawNet3 stage instance
            chunk_size: Chunk size in samples
            overlap: Overlap between chunks in samples
        """
        self.stage = stage
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process_large_audio(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Process large audio file in chunks.

        Args:
            audio: Input audio array

        Returns:
            Aggregated detection results
        """
        if len(audio) <= self.chunk_size:
            return self.stage.process(audio)

        # Split into chunks
        chunks = self._split_chunks(audio)
        chunk_results = []

        for i, chunk in enumerate(chunks):
            result = self.stage.process(chunk)
            chunk_results.append(result)

        # Aggregate results
        return self._aggregate_results(chunk_results)

    def _split_chunks(self, audio: np.ndarray) -> list:
        """Split audio into overlapping chunks."""
        chunks = []
        step = self.chunk_size - self.overlap

        for start in range(0, len(audio), step):
            end = min(start + self.chunk_size, len(audio))
            chunks.append(audio[start:end])
            if end == len(audio):
                break

        return chunks

    def _aggregate_results(self, results: list) -> Dict[str, Any]:
        """Aggregate chunk results."""
        if not results:
            return {"success": False, "error": "No results to aggregate"}

        scores = [r.get("score", 0.5) for r in results if r.get("success", False)]
        confidences = [r.get("confidence", 0.0) for r in results if r.get("success", False)]

        if not scores:
            return {"success": False, "error": "All chunks failed"}

        # Use maximum score (most suspicious chunk)
        max_score = float(max(scores))
        avg_confidence = float(np.mean(confidences))

        return {
            "success": True,
            "score": max_score,
            "avg_score": float(np.mean(scores)),
            "confidence": avg_confidence,
            "is_spoof": max_score > 0.5,
            "num_chunks": len(results),
            "chunk_scores": scores,
            "demo_mode": results[0].get("demo_mode", True),
        }
