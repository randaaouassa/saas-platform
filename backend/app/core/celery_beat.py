from celery.schedules import crontab

from app.core.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "analytics-rebuild-yesterday": {
        "task": "analytics.rebuild_all_yesterday",
        "schedule": crontab(hour=1, minute=0),
    },
    "cleanup-old-driver-positions": {
        "task": "default.cleanup_old_driver_positions",
        "schedule": crontab(hour=3, minute=0),
    },
    "cleanup-old-domain-events": {
        "task": "default.cleanup_old_domain_events",
        "schedule": crontab(hour=3, minute=30),
    },
}