"""
Middleware utilities for FastAPI applications.

Provides cross-cutting concerns like metrics collection, logging, and error handling.
"""

import logging
import time
from typing import Dict, Any, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Immutable snapshot of metrics at a point in time."""
    timestamp: float
    requests_total: int
    errors_total: int
    success_total: int
    avg_processing_time: float

    @property
    def error_rate(self) -> float:
        """Calculate error rate as a ratio."""
        if self.requests_total > 0:
            return self.errors_total / self.requests_total
        return 0.0


class MetricsMiddleware:
    """
    Thread-safe metrics collector for API monitoring.
    
    Hybrid approach: OOP for state management, FP for transformations.
    
    Example:
        metrics = MetricsMiddleware()
        
        @app.middleware("http")
        async def metrics_middleware(request, call_next):
            metrics.record_request()
            start_time = time.time()
            try:
                response = await call_next(request)
                metrics.record_processing(time.time() - start_time)
                return response
            except Exception as e:
                metrics.record_error(500, type(e).__name__)
                raise
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = threading.RLock()
        self._request_count = 0
        self._error_count = 0
        self._success_count = 0
        self._processing_times: deque = deque(maxlen=1000)
        self._start_time = time.time()
        self._error_types: Dict[str, int] = {}

    def record_request(self) -> None:
        """Record an incoming request."""
        with self._lock:
            self._request_count += 1

    def record_processing(self, processing_time: float) -> None:
        """Record successful processing time."""
        with self._lock:
            self._processing_times.append(processing_time)
            self._success_count += 1

    def record_error(self, status_code: int, error_type: str) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._error_count += 1
            key = f"{status_code}:{error_type}"
            self._error_types[key] = self._error_types.get(key, 0) + 1

    def get_snapshot(self) -> MetricSnapshot:
        """Get an immutable snapshot of current metrics."""
        with self._lock:
            return MetricSnapshot(
                timestamp=time.time(),
                requests_total=self._request_count,
                errors_total=self._error_count,
                success_total=self._success_count,
                avg_processing_time=self._calculate_avg_time(),
            )

    def _calculate_avg_time(self) -> float:
        """Calculate average processing time."""
        times = list(self._processing_times)
        return sum(times) / len(times) if times else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics as a dictionary."""
        snapshot = self.get_snapshot()
        return {
            "requests": {
                "total": snapshot.requests_total,
                "success": snapshot.success_total,
                "errors": snapshot.errors_total,
                "error_rate": round(snapshot.error_rate, 4),
            },
            "processing": {
                "avg_time_seconds": round(snapshot.avg_processing_time, 3),
            },
            "uptime_seconds": round(snapshot.timestamp - self._start_time, 2),
        }


class LoggingMiddleware:
    """
    Structured logging middleware for API requests.
    
    Example:
        logging_mw = LoggingMiddleware(logger)
        
        @app.middleware("http")
        async def logging_middleware(request, call_next):
            logging_mw.log_request(request)
            try:
                response = await call_next(request)
                logging_mw.log_response(response)
                return response
            except Exception as e:
                logging_mw.log_error(e)
                raise
    """

    def __init__(self, custom_logger: Optional[logging.Logger] = None):
        """Initialize with optional custom logger."""
        self._logger = custom_logger or logger

    def log_request(self, method: str, url: str, client: Optional[str] = None) -> None:
        """Log incoming request details."""
        request_info = {
            "method": method,
            "url": url,
            "client": client,
        }
        self._logger.info(f"Request: {request_info}")

    def log_response(self, status_code: int) -> None:
        """Log response status."""
        self._logger.info(f"Response: {status_code}")

    def log_error(self, error: Exception) -> None:
        """Log error with full traceback."""
        self._logger.error(f"Error: {str(error)}", exc_info=True)


def build_error_response(
    status_code: int,
    detail: str,
    request_path: str,
    error_type: str = "error",
) -> Dict[str, Any]:
    """
    Build a standardized error response.
    
    Pure function that creates consistent error payloads.
    
    Args:
        status_code: HTTP status code
        detail: Error message/description
        request_path: The request path that caused the error
        error_type: Category of error (e.g., "validation_error", "server_error")
    
    Returns:
        Dictionary with standardized error structure
    
    Example:
        error_response = build_error_response(
            status_code=400,
            detail="Invalid input format",
            request_path="/api/upload",
            error_type="validation_error"
        )
    """
    return {
        "error": {
            "type": error_type,
            "status_code": status_code,
            "detail": detail,
            "path": request_path,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
