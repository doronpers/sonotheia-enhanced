"""
Detection Pipeline Orchestrator

Main orchestrator for the 6-stage audio deepfake detection pipeline.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import numpy as np

from .config import DetectionConfig, get_default_config
from .stages import (
    FeatureExtractionStage,
    TemporalAnalysisStage,
    ArtifactDetectionStage,
    RawNet3Stage,
    FusionEngine,
    ExplainabilityStage,
    PhysicsAnalysisStage,
)
from .utils import load_audio, preprocess_audio, convert_numpy_types

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Detection job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DetectionJob:
    """Represents a detection job."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.progress: float = 0.0
        self.current_stage: Optional[str] = None


class DetectionPipeline:
    """
    6-Stage Audio Deepfake Detection Pipeline

    Stages:
    1. Feature Extraction - Extract acoustic features
    2. Temporal Analysis - Analyze temporal patterns
    3. Artifact Detection - Detect audio artifacts
    4. RawNet3 Neural - Deep learning detection
    5. Fusion Engine - Combine stage results
    6. Explainability - Generate explanations
    """

    def __init__(
        self,
        config: Optional[DetectionConfig] = None,
        max_workers: int = 4,
    ):
        """
        Initialize detection pipeline.

        Args:
            config: Detection configuration
            max_workers: Maximum worker threads for async processing
        """
        self.config = config or get_default_config()
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        # Initialize stages
        self._init_stages()

        # Job tracking
        self._jobs: Dict[str, DetectionJob] = {}

        logger.info(
            f"DetectionPipeline initialized: demo_mode={self.config.demo_mode}"
        )

    def _init_stages(self) -> None:
        """Initialize all pipeline stages."""
        cfg = self.config

        # Stage 1: Feature Extraction
        self.feature_extraction = FeatureExtractionStage(
            sample_rate=cfg.feature_extraction.sample_rate,
            n_fft=cfg.feature_extraction.n_fft,
            hop_length=cfg.feature_extraction.hop_length,
            win_length=cfg.feature_extraction.win_length,
            n_mfcc=cfg.feature_extraction.n_mfcc,
            n_lfcc=cfg.feature_extraction.n_lfcc,
            feature_types=cfg.feature_extraction.feature_types,
            include_deltas=cfg.feature_extraction.include_deltas,
        )

        # Stage 2: Temporal Analysis
        self.temporal_analysis = TemporalAnalysisStage(
            window_size=cfg.temporal_analysis.window_size,
            hop_size=cfg.temporal_analysis.hop_size,
            min_segment_length=cfg.temporal_analysis.min_segment_length,
            smoothing_window=cfg.temporal_analysis.smoothing_window,
            threshold_std_multiplier=cfg.temporal_analysis.threshold_std_multiplier,
            sample_rate=cfg.feature_extraction.sample_rate,
        )

        # Stage 3: Artifact Detection
        self.artifact_detection = ArtifactDetectionStage(
            sample_rate=cfg.feature_extraction.sample_rate,
            silence_threshold_db=cfg.artifact_detection.silence_threshold_db,
            min_silence_duration=cfg.artifact_detection.min_silence_duration,
            click_threshold=cfg.artifact_detection.click_threshold,
            click_min_gap=cfg.artifact_detection.click_min_gap,
        )

        # Stage 4: RawNet3 Neural
        self.rawnet3 = RawNet3Stage(
            config=cfg.rawnet3,
            demo_mode=cfg.demo_mode,
        )

        # Stage 5: Fusion Engine
        self.fusion_engine = FusionEngine(
            fusion_method=cfg.fusion_engine.fusion_method,
            stage_weights=cfg.fusion_engine.stage_weights,
            confidence_threshold=cfg.fusion_engine.confidence_threshold,
            decision_threshold=cfg.fusion_engine.decision_threshold,
        )

        # Stage 3b: Physics Analysis
        self.physics_analysis = PhysicsAnalysisStage(
            config=cfg.physics_analysis
        )

        # Stage 6: Explainability
        self.explainability = ExplainabilityStage(
            generate_saliency=cfg.explainability.generate_saliency,
            include_feature_importance=cfg.explainability.include_feature_importance,
            include_temporal_segments=cfg.explainability.include_temporal_segments,
            max_top_features=cfg.explainability.max_top_features,
            detail_level=cfg.explainability.explanation_detail_level,
        )

    def detect(
        self,
        audio_source: Union[str, bytes, np.ndarray, Path],
        quick_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Run detection pipeline on audio.

        Args:
            audio_source: Audio file path, bytes, or array
            quick_mode: Run only stages 1-3 for quick detection

        Returns:
            Detection result with scores and explanations
        """
        job_id = str(uuid.uuid4())
        job = DetectionJob(job_id)
        self._jobs[job_id] = job

        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)

            # Load and preprocess audio
            job.current_stage = "preprocessing"
            audio = self._prepare_audio(audio_source)

            # Validate audio
            duration = len(audio) / self.config.feature_extraction.sample_rate
            if duration < self.config.min_audio_duration:
                raise ValueError(
                    f"Audio too short: {duration:.2f}s < {self.config.min_audio_duration}s"
                )
            if duration > self.config.max_audio_duration:
                raise ValueError(
                    f"Audio too long: {duration:.2f}s > {self.config.max_audio_duration}s"
                )

            # Run pipeline
            if quick_mode:
                result = self._run_quick_pipeline(audio, job)
            else:
                result = self._run_full_pipeline(audio, job)

            # OPTIMIZATION: Remove heavy raw feature arrays to significantly reduce JSON size (from ~45MB to ~50KB)
            # We only keep stats, scores, and lightweight metadata.
            if "stage_results" in result and "feature_extraction" in result["stage_results"]:
                fe_res = result["stage_results"]["feature_extraction"]
                fe_res.pop("features", None)
                fe_res.pop("combined_features", None)

            # Ensure JSON serializable
            result = convert_numpy_types(result)

            # Add metadata
            result["job_id"] = job_id
            result["duration_seconds"] = duration
            result["quick_mode"] = quick_mode
            result["demo_mode"] = self.config.demo_mode
            result["timestamp"] = datetime.now(timezone.utc).isoformat()

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.result = result
            job.progress = 1.0

            return result

        except Exception as e:
            logger.error(f"Detection failed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)

            return convert_numpy_types({
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    def detect_async(
        self,
        audio_source: Union[str, bytes, np.ndarray, Path],
        quick_mode: bool = False,
    ) -> str:
        """
        Start async detection and return job ID.

        Args:
            audio_source: Audio file path, bytes, or array
            quick_mode: Run only stages 1-3

        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        job = DetectionJob(job_id)
        self._jobs[job_id] = job

        # Submit to executor
        self._executor.submit(self._run_async_job, job_id, audio_source, quick_mode)

        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of detection job."""
        job = self._jobs.get(job_id)
        if job is None:
            return {"error": f"Job {job_id} not found"}

        return {
            "job_id": job_id,
            "status": job.status.value,
            "progress": job.progress,
            "current_stage": job.current_stage,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
        }

    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get result of completed job."""
        job = self._jobs.get(job_id)
        if job is None:
            return {"error": f"Job {job_id} not found"}

        if job.status != JobStatus.COMPLETED:
            return {
                "error": f"Job not completed (status: {job.status.value})",
                "status": job.status.value,
            }

        return job.result

    def _prepare_audio(self, audio_source: Union[str, bytes, np.ndarray, Path]) -> np.ndarray:
        """Load and preprocess audio."""
        if isinstance(audio_source, np.ndarray):
            audio = audio_source.astype(np.float32)
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / 32768.0  # Assume int16 range
        else:
            audio, sr = load_audio(
                audio_source,
                target_sr=self.config.feature_extraction.sample_rate,
            )

        # Preprocess
        audio = preprocess_audio(
            audio,
            sr=self.config.feature_extraction.sample_rate,
            normalize=True,
            trim=True,
        )

        return audio

    def _run_full_pipeline(self, audio: np.ndarray, job: DetectionJob) -> Dict[str, Any]:
        """Run complete 6-stage pipeline."""
        stage_results = {}

        # Stage 1: Feature Extraction
        job.current_stage = "feature_extraction"
        job.progress = 0.1
        stage_results["feature_extraction"] = self.feature_extraction.process(audio)
        logger.debug("Stage 1 (Feature Extraction) complete")

        # Stage 2: Temporal Analysis
        job.current_stage = "temporal_analysis"
        job.progress = 0.25
        features = stage_results["feature_extraction"].get("combined_features")
        stage_results["temporal_analysis"] = self.temporal_analysis.process(
            audio, features
        )
        logger.debug("Stage 2 (Temporal Analysis) complete")

        # Stage 3: Artifact Detection
        job.current_stage = "artifact_detection"
        job.progress = 0.4
        stage_results["artifact_detection"] = self.artifact_detection.process(audio)
        logger.debug("Stage 3 (Artifact Detection) complete")

        # Stage 3b: Physics Analysis
        job.current_stage = "physics_analysis"
        # Adjusted progress markers to fit new stage
        job.progress = 0.5
        stage_results["physics_analysis"] = self.physics_analysis.process(audio)
        logger.debug("Stage 3b (Physics Analysis) complete")

        # Stage 4: RawNet3 Neural
        job.current_stage = "rawnet3"
        job.progress = 0.6
        stage_results["rawnet3"] = self.rawnet3.process(audio)
        logger.debug("Stage 4 (RawNet3) complete")

        # Stage 5: Fusion
        job.current_stage = "fusion"
        job.progress = 0.8
        fusion_result = self.fusion_engine.fuse(stage_results)
        logger.debug("Stage 5 (Fusion) complete")

        # Stage 6: Explainability
        job.current_stage = "explainability"
        job.progress = 0.9
        explainability_result = self.explainability.process(stage_results, fusion_result)
        logger.debug("Stage 6 (Explainability) complete")

        return {
            "success": True,
            "detection_score": fusion_result.get("fused_score", 0.5),
            "is_spoof": fusion_result.get("is_spoof", False),
            "confidence": fusion_result.get("confidence", 0.0),
            "decision": fusion_result.get("decision", "UNCERTAIN"),
            "fusion_result": fusion_result,
            "stage_results": stage_results,
            "explanation": explainability_result,
        }

    def _run_quick_pipeline(self, audio: np.ndarray, job: DetectionJob) -> Dict[str, Any]:
        """Run quick detection (stages 1-3 only)."""
        stage_results = {}

        # Stage 1: Feature Extraction
        job.current_stage = "feature_extraction"
        job.progress = 0.2
        stage_results["feature_extraction"] = self.feature_extraction.process(audio)

        # Stage 2: Temporal Analysis
        job.current_stage = "temporal_analysis"
        job.progress = 0.5
        features = stage_results["feature_extraction"].get("combined_features")
        stage_results["temporal_analysis"] = self.temporal_analysis.process(
            audio, features
        )

        # Stage 3: Artifact Detection
        job.current_stage = "artifact_detection"
        job.progress = 0.8
        stage_results["artifact_detection"] = self.artifact_detection.process(audio)

        # Quick fusion using only available stages
        quick_fusion = FusionEngine(
            stage_weights={
                "feature_extraction": 0.33,
                "temporal_analysis": 0.33,
                "artifact_detection": 0.34,
            }
        )
        fusion_result = quick_fusion.fuse(stage_results)

        return {
            "success": True,
            "detection_score": fusion_result.get("fused_score", 0.5),
            "is_spoof": fusion_result.get("is_spoof", False),
            "confidence": fusion_result.get("confidence", 0.0),
            "decision": fusion_result.get("decision", "UNCERTAIN"),
            "fusion_result": fusion_result,
            "stage_results": stage_results,
            "explanation": {
                "summary": f"Quick detection completed with score {fusion_result.get('fused_score', 0.5):.3f}",
                "note": "Quick mode only runs acoustic analysis (stages 1-3). Use full mode for neural network analysis.",
            },
        }

    def _run_async_job(
        self,
        job_id: str,
        audio_source: Union[str, bytes, np.ndarray, Path],
        quick_mode: bool,
    ) -> None:
        """Run detection job asynchronously."""
        try:
            self.detect(audio_source, quick_mode)
            # Result is stored in job by detect() method
        except Exception as e:
            logger.error(f"Async job {job_id} failed: {e}")
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.utcnow()


# Singleton instance for API usage
_pipeline_instance: Optional[DetectionPipeline] = None


def get_pipeline() -> DetectionPipeline:
    """Get or create pipeline singleton."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DetectionPipeline()
    return _pipeline_instance
