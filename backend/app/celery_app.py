from celery import Celery
from app.config import settings

celery_app = Celery(
    "fltect",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Try to connect to Redis; if unavailable, use eager mode (synchronous)
try:
    import redis
    r = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
    r.ping()
    celery_app.conf.update(task_always_eager=False)
except Exception:
    celery_app.conf.update(task_always_eager=True)

celery_app.autodiscover_tasks(["app.tasks"])
