from app.core.celery_app import celery_app


def test_queues_configured():
    qs = {q.name for q in celery_app.conf.task_queues}
    assert {"default", "notifications", "routing", "analytics", "dlq"} <= qs


def test_routes():
    routes = celery_app.conf.task_routes
    assert "app.modules.notifications.*" in routes
    assert routes["app.modules.notifications.*"]["queue"] == "notifications"


def test_retry_policy():
    assert celery_app.conf.task_max_retries >= 3
    assert celery_app.conf.task_default_retry_delay >= 5


def test_beat_schedule_loaded():
    # importing celery_beat triggers schedule assignment
    import app.core.celery_beat  # noqa: F401

    sched = celery_app.conf.beat_schedule
    assert "analytics-rebuild-yesterday" in sched
    assert "cleanup-old-driver-positions" in sched


def test_time_limits():
    assert celery_app.conf.task_time_limit > 0
    assert celery_app.conf.task_soft_time_limit > 0