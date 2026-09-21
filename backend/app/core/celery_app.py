from celery import Celery

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
    task_routes={
        "app.modules.notifications.*": {"queue": "notifications"},
        "app.modules.routing.*": {"queue": "routing"},
        "app.modules.analytics.*": {"queue": "analytics"},
    },
    task_default_retry_delay=10,
    task_max_retries=5,
    broker_connection_retry_on_startup=True,
)