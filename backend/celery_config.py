"""
Celery Configuration Module
Defines all Celery settings including broker, backend, task routing, and retry policies.
"""

import os

# Broker and Backend URLs
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Task Queues Configuration
CELERY_TASK_QUEUES = {
    "default": {"binding_key": "default"},
    "audio": {"binding_key": "audio"},
    "detection": {"binding_key": "detection"},
    "analysis": {"binding_key": "analysis"},
    "sar": {"binding_key": "sar"},
}

# Task Routing
CELERY_TASK_ROUTES = {
    "tasks.audio_tasks.*": {"queue": "audio"},
    "tasks.detection_tasks.*": {"queue": "detection"},
    "tasks.analysis_tasks.*": {"queue": "analysis"},
    "tasks.sar_tasks.*": {"queue": "sar"},
}

# Serialization - Use JSON for safety (no pickle)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Task Execution Settings
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes soft limit
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes hard limit
CELERY_TASK_ACKS_LATE = True  # Acknowledge after task completes
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Retry Settings
CELERY_TASK_DEFAULT_RETRY_DELAY = 30  # 30 seconds between retries
CELERY_TASK_MAX_RETRIES = 3

# Worker Settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # One task at a time for memory-intensive tasks
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Restart worker after 100 tasks (memory cleanup)

# Result Backend Settings
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_RESULT_EXTENDED = True  # Store additional info about tasks

# Task Priority (1-10, 1 is highest)
CELERY_TASK_DEFAULT_PRIORITY = 5
CELERY_TASK_PRIORITY_WEIGHTS = {
    "high": 3,
    "normal": 5,
    "low": 7,
}

# Visibility Timeout for long-running tasks
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 3600,  # 1 hour
}


def get_celery_config():
    """
    Return Celery configuration as a dictionary.

    Returns:
        dict: Celery configuration settings
    """
    return {
        "broker_url": CELERY_BROKER_URL,
        "result_backend": CELERY_RESULT_BACKEND,
        "task_serializer": CELERY_TASK_SERIALIZER,
        "result_serializer": CELERY_RESULT_SERIALIZER,
        "accept_content": CELERY_ACCEPT_CONTENT,
        "task_soft_time_limit": CELERY_TASK_SOFT_TIME_LIMIT,
        "task_time_limit": CELERY_TASK_TIME_LIMIT,
        "task_acks_late": CELERY_TASK_ACKS_LATE,
        "task_reject_on_worker_lost": CELERY_TASK_REJECT_ON_WORKER_LOST,
        "task_default_retry_delay": CELERY_TASK_DEFAULT_RETRY_DELAY,
        "worker_prefetch_multiplier": CELERY_WORKER_PREFETCH_MULTIPLIER,
        "worker_concurrency": CELERY_WORKER_CONCURRENCY,
        "worker_max_tasks_per_child": CELERY_WORKER_MAX_TASKS_PER_CHILD,
        "result_expires": CELERY_RESULT_EXPIRES,
        "result_extended": CELERY_RESULT_EXTENDED,
        "broker_transport_options": CELERY_BROKER_TRANSPORT_OPTIONS,
        "task_routes": CELERY_TASK_ROUTES,
    }
