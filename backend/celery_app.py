"""
Celery Application Configuration
Main entry point for Celery task queue application.
"""

from celery import Celery, signals
from celery_config import get_celery_config
import logging

logger = logging.getLogger(__name__)

# Create Celery application
app = Celery("sonotheia")

# Load configuration
app.config_from_object(get_celery_config())

# Auto-discover tasks from the tasks package
app.autodiscover_tasks(["tasks"])


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok", "task_id": self.request.id, "message": "Celery is working correctly"}


# Signal handlers for worker lifecycle
@signals.worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    """Handle worker ready signal."""
    logger.info(f"Worker {sender} is ready")


@signals.worker_shutting_down.connect
def worker_shutdown_handler(sender, sig, how, exitcode, **kwargs):
    """Handle worker shutdown signal."""
    logger.info(f"Worker {sender} is shutting down (signal: {sig}, how: {how})")


@signals.task_prerun.connect
def task_prerun_handler(sender, task_id, task, args, kwargs, **extra):
    """Handle task prerun signal."""
    logger.info(f"Task {task.name}[{task_id}] is starting")


@signals.task_postrun.connect
def task_postrun_handler(sender, task_id, task, args, kwargs, retval, state, **extra):
    """Handle task postrun signal."""
    logger.info(f"Task {task.name}[{task_id}] completed with state: {state}")


@signals.task_failure.connect
def task_failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo, **extra):
    """Handle task failure signal."""
    logger.error(f"Task {sender.name}[{task_id}] failed: {exception}")


if __name__ == "__main__":
    app.start()
