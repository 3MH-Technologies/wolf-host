from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("wolfhost", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "monitor-bots-health": {
        "task": "app.workers.tasks.monitor_bots_health",
        "schedule": 30.0,
    },
    "expire-pending-invoices": {
        "task": "app.workers.tasks.expire_pending_invoices",
        "schedule": crontab(minute="*/15"),
    },
    "expire-subscriptions": {
        "task": "app.workers.tasks.expire_subscriptions",
        "schedule": crontab(minute=0),
    },
}
