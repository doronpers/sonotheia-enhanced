"""
Celery Utility Functions
Helpers for task management, serialization, chaining, and error handling.
"""

import numpy as np
from typing import Any, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def numpy_to_native(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types for JSON serialization.

    Args:
        obj: Object to convert (can be numpy array, dict, list, or scalar)

    Returns:
        Object with all numpy types converted to native Python types
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [numpy_to_native(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def serialize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a task result for safe JSON storage.

    Args:
        result: Task result dictionary

    Returns:
        Serialized result with no numpy types
    """
    serialized = numpy_to_native(result)

    # Add metadata
    serialized["_serialized_at"] = datetime.now().isoformat()

    return serialized


def create_task_result(
    status: str, data: Dict[str, Any] = None, error: str = None, progress: float = None, message: str = None
) -> Dict[str, Any]:
    """
    Create a standardized task result.

    Args:
        status: Task status (PENDING, STARTED, PROCESSING, COMPLETED, FAILED)
        data: Result data
        error: Error message if failed
        progress: Progress percentage (0-100)
        message: Status message

    Returns:
        Standardized task result dictionary
    """
    result = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    if data is not None:
        result["data"] = numpy_to_native(data)

    if error is not None:
        result["error"] = str(error)

    if progress is not None:
        result["progress"] = float(progress)

    if message is not None:
        result["message"] = str(message)

    return result


def update_task_progress(task, progress: float, message: str = None):
    """
    Update task progress in a consistent way.

    Args:
        task: Celery task instance (with bind=True)
        progress: Progress percentage (0-100)
        message: Optional progress message
    """
    state_meta = {
        "progress": progress,
        "timestamp": datetime.now().isoformat(),
    }
    if message:
        state_meta["message"] = message

    task.update_state(state="PROCESSING", meta=state_meta)


def handle_task_error(task, error: Exception, retryable: bool = True):
    """
    Handle task errors in a consistent way.

    Args:
        task: Celery task instance
        error: The exception that occurred
        retryable: Whether the task should be retried

    Raises:
        The original exception after logging and optional retry
    """
    logger.error(f"Task {task.name}[{task.request.id}] failed: {str(error)}", exc_info=True)

    if retryable and task.request.retries < task.max_retries:
        logger.info(
            f"Retrying task {task.name}[{task.request.id}] " f"(attempt {task.request.retries + 1}/{task.max_retries})"
        )
        raise task.retry(exc=error)

    raise error


def estimate_time_remaining(progress: float, elapsed_seconds: float) -> float:
    """
    Estimate remaining time based on current progress.

    Args:
        progress: Current progress (0-100)
        elapsed_seconds: Time elapsed so far

    Returns:
        Estimated remaining time in seconds
    """
    if progress <= 0:
        return 0.0

    rate = progress / elapsed_seconds
    remaining_progress = 100 - progress

    return remaining_progress / rate if rate > 0 else 0.0


def validate_audio_data(audio_data: bytes, max_size_mb: int = 15) -> bool:
    """
    Validate audio data before processing.

    Args:
        audio_data: Raw audio bytes
        max_size_mb: Maximum allowed size in MB

    Returns:
        True if valid

    Raises:
        ValueError: If audio data is invalid
    """
    if not audio_data:
        raise ValueError("Audio data is empty")

    max_bytes = max_size_mb * 1024 * 1024
    if len(audio_data) > max_bytes:
        raise ValueError(f"Audio data exceeds maximum size of {max_size_mb}MB")

    return True


def safe_cleanup(resources: List[Any], cleanup_fn=None):
    """
    Safely cleanup resources after task completion or failure.

    Args:
        resources: List of resources to cleanup
        cleanup_fn: Optional custom cleanup function (callable)
    """
    for resource in resources:
        try:
            if cleanup_fn:
                cleanup_fn(resource)
            elif hasattr(resource, "close"):
                resource.close()
        except Exception as e:
            logger.warning(f"Failed to cleanup resource: {e}")


class TaskChain:
    """Helper class for building task chains."""

    def __init__(self, initial_task):
        """Initialize chain with first task."""
        self._chain = initial_task

    def then(self, next_task):
        """Add next task in chain."""
        from celery import chain

        self._chain = chain(self._chain, next_task)
        return self

    def apply_async(self, **kwargs):
        """Execute the chain asynchronously."""
        return self._chain.apply_async(**kwargs)

    def delay(self, *args, **kwargs):
        """Execute the chain with delay."""
        return self._chain.delay(*args, **kwargs)
