from celery import Celery
from app.config import settings

celery_app = Celery(
    "aegisscan",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.worker"],
)

celery_app.conf.task_track_started=True