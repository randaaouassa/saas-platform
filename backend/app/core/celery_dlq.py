import structlog
from celery.signals import task_failure

from app.core.celery_app import celery_app

log = structlog.get_logger("celery.dlq")


@celery_app.task(name="default.dlq_replay", queue="dlq")
def dlq_replay(task_name: str, args: list, kwargs: dict) -> str:
    log.info("dlq_replay", task=task_name)
    return celery_app.send_task(task_name, args=args, kwargs=kwargs).id


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, **_):
    if sender is None:
        return
    retries = getattr(sender.request, "retries", 0)
    max_retries = getattr(sender, "max_retries", 3)
    if retries >= max_retries:
        log.error(
            "task_moved_to_dlq",
            task=sender.name,
            task_id=task_id,
            error=str(exception),
            retries=retries,
        )
        celery_app.send_task(
            "default.dlq_replay",
            args=[sender.name, list(args or []), dict(kwargs or {})],
            queue="dlq",
        )