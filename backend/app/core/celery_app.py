from celery import Celery
from kombu import Queue

from app.core.config import settings

celery_app = Celery(
    "saas_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("notifications", routing_key="notifications"),
        Queue("routing", routing_key="routing"),
        Queue("analytics", routing_key="analytics"),
        Queue("dlq", routing_key="dlq"),
    ),
    task_routes={
        "app.modules.notifications.*": {"queue": "notifications"},
        "app.modules.routing.*": {"queue": "routing"},
        "app.modules.analytics.*": {"queue": "analytics"},
        "dispatch.*": {"queue": "routing"},
    },
    task_default_retry_delay=10,
    task_max_retries=5,
    task_time_limit=600,
    task_soft_time_limit=540,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    beat_schedule_filename="/tmp/celerybeat-schedule",
)

celery_app.autodiscover_tasks(
    [
        "app.modules.notifications.tasks",
        "app.modules.analytics.tasks",
        "app.modules.dispatch.tasks",
    ]
)