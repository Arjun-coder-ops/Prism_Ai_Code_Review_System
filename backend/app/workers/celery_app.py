from celery import Celery
from app.core.config import get_settings

celery_app = Celery("prism", broker=get_settings().redis_url, backend=get_settings().redis_url)
celery_app.conf.update(task_default_queue="reviews", task_serializer="json", accept_content=["json"], result_serializer="json", task_acks_late=True, worker_prefetch_multiplier=1)


@celery_app.task(name="prism.healthcheck")
def healthcheck() -> str:
    return "ok"
