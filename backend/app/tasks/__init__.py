from celery import Celery

from app.config import settings

celery_app = Celery(
    "movie_discovery",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-trending-every-6-hours": {
            "task": "app.tasks.sync_tasks.sync_trending_movies",
            "schedule": 21600.0,
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
