from celery import shared_task

from app.utils.logger import logger


@shared_task(
    bind=True,
)
def task_test(self):
    logger.info(f"Executing task_test with id: {self.request.id}")
    return "Task test completed successfully."
