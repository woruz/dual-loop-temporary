from celery import Celery

# Initialize Celery app.
# In production, the broker/backend URLs are loaded from configurations/env variables.
celery_app = Celery(
    "dual_loop_workers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.server.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
