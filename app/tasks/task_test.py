
from app.utils.logger import logger


def task_test(self):
    logger.info(f"Executing task_test with id: {self.request.id}")
    return "Task test completed successfully."
