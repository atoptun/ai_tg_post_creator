from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.config import settings
from app.utils.logger import logger
# from app.infra.mongo import get_mongo_client_sync, close_mongo_client_sync


celery_app = Celery(
    "celery_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@worker_process_init.connect
def on_worker_process_init(**kwargs):
    # get_mongo_client_sync()
    logger.info("Worker process initialized.")


@worker_process_shutdown.connect
def on_worker_process_shutdown(**kwargs):
    # close_mongo_client_sync()
    logger.info("Worker process shutting down.")


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

celery_app.autodiscover_tasks([
    "app.tasks.task_test",
])
